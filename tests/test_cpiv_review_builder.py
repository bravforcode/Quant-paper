from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from scripts.build_cpiv_review import (
    _example_metrics,
    add_table_borders,
    docx_args_without_toc,
    interactive_widget,
    load_noise_results,
    number_html_figure_captions,
    patch_docx_figure_captions_and_wide_table_pagebreaks,
    postprocess_html,
    prepare_r22_pdf_source_text,
    resolve_source_path,
)

NOISE_LEVELS = (0.0, 0.10, 0.20, 0.35, 0.50, 1.0, 2.0)


def test_non_default_revision_requires_explicit_source() -> None:
    with pytest.raises(ValueError, match="pass --source explicitly"):
        resolve_source_path("r22", None)


def test_default_revision_uses_default_source() -> None:
    assert resolve_source_path("r8", None).name == "manuscript_r8.md"


def test_docx_args_omit_unpopulated_word_toc() -> None:
    common = [
        "manuscript.md",
        "--from=markdown",
        "--resource-path=.",
        "--toc",
        "--toc-depth=2",
    ]
    assert docx_args_without_toc(common) == common[:3]


def _noise_row(
    target: float,
    order: list[str] | None = None,
    magnitude: float = 5.0,
) -> dict[str, object]:
    names = order or [f"SIM{index:02d}" for index in range(1, 11)]
    ranked = [
        {
            "symbol": name,
            "cpiv_pp": (rank - 5) * magnitude / 5,
            "rank_low_to_high": rank,
        }
        for rank, name in enumerate(names, start=1)
    ]
    return {
        "target_cpiv_noise_sd_pp": target,
        "replicates": 2000,
        "rank_inversions_p05": 0.0,
        "rank_inversions_median": 1.0,
        "rank_inversions_p95": 4.0,
        "spearman_rho_p05": 0.80,
        "spearman_rho_median": 0.90,
        "spearman_rho_p95": 0.98,
        "probability_no_pairwise_inversions": 0.40,
        "probability_any_extreme_quintile_crossover": 0.01,
        "probability_long_short_membership_change": 0.55,
        "example_ranked_names": ranked,
    }


def test_add_table_borders_adds_grid_to_each_docx_table(tmp_path: Path) -> None:
    docx_path = tmp_path / "tables.docx"
    document_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:tbl><w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:type="auto" w:w="0"/>
          <w:tblLayout w:type="fixed"/><w:tblLook/></w:tblPr></w:tbl>
        <w:tbl><w:tblPr><w:tblW w:type="auto" w:w="0"/></w:tblPr></w:tbl>
      </w:body>
    </w:document>'''
    with ZipFile(docx_path, "w") as package:
        package.writestr("word/document.xml", document_xml)

    add_table_borders(docx_path)
    with ZipFile(docx_path) as package:
        assert package.testzip() is None
        bordered_xml = package.read("word/document.xml")
    add_table_borders(docx_path)
    with ZipFile(docx_path) as package:
        assert package.read("word/document.xml") == bordered_xml

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = ET.fromstring(bordered_xml)
    tables = root.findall(".//w:tbl", ns)
    assert len(tables) == 2
    edges = {"top", "left", "bottom", "right", "insideH", "insideV"}
    for table in tables:
        borders = table.find("./w:tblPr/w:tblBorders", ns)
        assert borders is not None
        assert {edge.tag.rsplit("}", 1)[-1] for edge in borders} == edges
    properties = tables[0].find("./w:tblPr", ns)
    assert properties is not None
    property_order = [child.tag.rsplit("}", 1)[-1] for child in properties]
    assert property_order.index("tblBorders") < property_order.index("tblLayout")


def test_docx_figure_labels_and_wide_table_pagebreaks_are_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "captions.docx"
    captions = b"".join(
        f'<w:p><w:pPr><w:pStyle w:val="ImageCaption"/></w:pPr>'
        f'<w:r><w:t>Caption {i}</w:t></w:r></w:p>'.encode()
        for i in range(1, 4)
    )
    table5 = (
        b'<w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr>'
        b'<w:r><w:t>Table 5.</w:t></w:r></w:p>'
    )
    table6 = (
        b'<w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr>'
        b'<w:r><w:t>Table 6.</w:t></w:r></w:p>'
    )
    table7 = (
        b'<w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr>'
        b'<w:r><w:t>Table 7.</w:t></w:r></w:p>'
    )
    table10 = (
        b'<w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr>'
        b'<w:r><w:t>Table 10.</w:t></w:r></w:p>'
    )
    protocol_lead = (
        b'<w:p><w:r><w:t>The proposed staged checklist for future paired-option analyses '
        b'is the protocol lead.</w:t></w:r></w:p>'
    )
    with ZipFile(path, "w") as package:
        package.writestr(
            "word/document.xml",
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            + b"<w:body>"
            + captions
            + table5
            + table6
            + table7
            + protocol_lead
            + table10
            + b"</w:body></w:document>",
        )

    patch_docx_figure_captions_and_wide_table_pagebreaks(path)
    patch_docx_figure_captions_and_wide_table_pagebreaks(path)
    with ZipFile(path) as package:
        xml = package.read("word/document.xml")
        assert package.testzip() is None
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = root.findall(".//w:p", ns)
    figure_text = ["".join(node.itertext()) for node in paragraphs[:3]]
    assert figure_text == [
        "Figure 1: Caption 1",
        "Figure 2: Caption 2",
        "Figure 3: Caption 3",
    ]
    assert len(root.findall(".//w:pageBreakBefore", ns)) == 4


def test_html_figure_labels_are_single_and_stable() -> None:
    page = (
        "<figcaption>Caption one</figcaption>"
        "<figcaption>Figure 2. Caption two</figcaption>"
        "<figcaption>Caption three</figcaption>"
    )
    numbered = number_html_figure_captions(page)
    assert numbered.count("Figure 1:") == 1
    assert numbered.count("Figure 2:") == 1
    assert numbered.count("Figure 3:") == 1
    assert number_html_figure_captions(numbered) == numbered


def test_r22_pdf_source_starts_american_figure_and_wide_tables_on_fresh_pages() -> None:
    figure = (
        "![CRR and equal-probability Jarrow–Rudd American-put synthetic tree comparison.]"
    )
    source = (
        f"Before.\n\n{figure}{{#fig-american-convergence}}\n\n"
        "**Table 3.** Ranking\n\n"
        "### 7.7 Price identification and tolerance\n\n"
        "## 8. Interpretation and limits\n\n"
        "The proposed staged checklist for future paired-option work is summarized in Table 10. "
        "It is an operational protocol.\n\n**Table 10.** Protocol"
    )
    prepared = prepare_r22_pdf_source_text(source)
    assert prepared.count("\\newpage") == 4
    assert prepared.index("\\newpage\n\n" + figure) > prepared.index("Before.")
    assert prepared.index("\\newpage\n\n**Table 3.**") > prepared.index(figure)
    assert prepared.index(
        "\\newpage\n\n## 8. Interpretation and limits"
    ) > prepared.index(figure)
    lead = "The proposed staged checklist for future paired-option work is summarized in Table 10."
    assert prepared.index("\\newpage\n\n" + lead) > prepared.index(
        "## 8. Interpretation and limits"
    )
    assert prepared.index("**Table 10.** Protocol") > prepared.index(
        "## 8. Interpretation and limits"
    )
    assert prepared.index("**Table 10.** Protocol") > prepared.index(
        "### 7.7 Price identification and tolerance"
    )
    assert "\\newpage\n\n**Table 10.**" not in prepared
    with pytest.raises(ValueError, match="exactly one Table 3 caption"):
        prepare_r22_pdf_source_text(
            f"{figure} ## 8. Interpretation and limits "
            f"{lead} **Table 10.** no Table 3"
        )


def test_r10_widget_is_labeled_as_r8_appendix_and_commands_are_present() -> None:
    manuscript_path = (
        Path(__file__).resolve().parents[1]
        / "research" / "cpiv" / "manuscript_r10_proposed.md"
    )
    source = manuscript_path.read_text(encoding="utf-8")
    appendix = source.index("## Appendix A. R8 baseline illustration (not an R10 result)")
    widget = source.index("<!-- CPIV_INTERACTIVE_WIDGET -->")
    reproduction = source.index("## Appendix B. Reproduction commands")
    references = source.index("## References")
    assert appendix < widget < reproduction < references
    assert "-m research.cpiv.build_demo" in source
    assert "-m research.cpiv.r10_diagnostics" in source
    assert "research/cpiv/generated/r10_release" in source
    assert "-m research.cpiv.independent_bsm_crosscheck" in source
    assert "-m research.cpiv.near_bound_decimal_audit" in source
    assert "manifest.sha256" in source
    assert "Get-FileHash" in source
    assert "revision_20261010_r10_proposed_final6" not in source
    assert "revision_20261009_r10_proposed_final5" not in source


def test_widget_renders_representative_ranks_from_noise_data() -> None:
    rows = [_noise_row(level, magnitude=5 + 2 * level) for level in NOISE_LEVELS]
    widget = interactive_widget(rows)
    assert "example_ranked_names" in widget
    assert "document.createElement" in widget
    assert "cpiv-noise-ranking" in widget
    assert "half_spread_usd_per_option" not in widget
    assert 'data-axis-limit-pp="9.0"' in widget
    assert 'value="2" aria-valuetext="0.20 pp"' in widget
    assert 'class="noise-level-label is-current">0.20</span>' in widget
    assert widget.count('<span class="noise-level-label') == 7
    assert "id=\"cpiv-mc-summary\">Across 2,000 Monte Carlo replicates" in widget
    assert "ρ median 0.900 (p05–p95 0.800–0.980)" in widget
    assert "pairwise inversions median 1 (p05–p95 0–4)" in widget
    assert "One stored example draw" in widget
    assert "not a Monte Carlo average" in widget
    assert "empirical quantiles" in widget
    assert "<noscript>" in widget
    assert "width:30.00%" in widget
    assert "const maxMagnitude" not in widget
    html_without_script = widget.split("<script>", 1)[0]
    assert html_without_script.count('<li class="rank-row">') == 10
    assert 'id="cpiv-mc-summary">Across 2,000 Monte Carlo replicates' in html_without_script
    assert 'id="cpiv-example-summary">One stored example draw' in html_without_script
    assert "<noscript>" in html_without_script


def test_single_stored_example_metrics_are_not_monte_carlo_aggregates() -> None:
    baseline = _noise_row(0.0)
    swapped = _noise_row(
        1.0,
        ["SIM02", "SIM01", *[f"SIM{index:02d}" for index in range(3, 11)]],
    )

    metrics = _example_metrics(swapped, baseline)

    assert metrics["inversions"] == 1
    assert metrics["spearman_rho"] == pytest.approx(0.9878787878787879)
    assert metrics["extreme_membership_changed"] is False
    assert swapped["probability_long_short_membership_change"] == 0.55


def test_load_noise_results_requires_all_seven_widget_levels(tmp_path: Path) -> None:
    path = tmp_path / "stress.json"
    rows = [_noise_row(level) for level in NOISE_LEVELS]
    path.write_text(
        json.dumps(
            {
                "status": "synthetic_sensitivity_analysis_only",
                "market_data_used": False,
                "quote_noise_ranking": {
                    "seed": 20261008,
                    "replicates": 2000,
                    "results": rows,
                },
            }
        ),
        encoding="utf-8",
    )

    assert len(load_noise_results(path, replicates=2000)) == 7

    path.write_text(
        json.dumps(
            {
                "status": "synthetic_sensitivity_analysis_only",
                "market_data_used": False,
                "quote_noise_ranking": {
                    "seed": 20261008,
                    "replicates": 2000,
                    "results": rows[:-1],
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="seven declared noise levels"):
        load_noise_results(path, replicates=2000)


def test_postprocess_embeds_social_card_after_charset_and_preserves_widget(tmp_path: Path) -> None:
    html_path = tmp_path / "paper.html"
    card_path = tmp_path / "social-card.png"
    card_path.write_bytes(b"synthetic-test-image")
    html_path.write_text(
        '<!doctype html><html><head><meta charset="utf-8" /></head><body>'
        '<h1 class="title">CPIV</h1><math></math>'
        '<img src="data:image/png;base64,YQ==" alt="figure">'
        '<!-- CPIV_INTERACTIVE_WIDGET --></body></html>',
        encoding="utf-8",
    )
    postprocess_html(
        html_path,
        [_noise_row(0.0)],
        card_path,
        title="R9 title",
        description="R9 description",
    )
    page = html_path.read_text(encoding="utf-8")
    assert page.index('charset="utf-8"') < page.index('property="og:title"')
    assert 'name="author" content="Phirawit Jitnarong"' in page
    assert 'property="og:locale" content="th_TH"' in page
    assert 'property="og:title" content="R9 title"' in page
    assert 'property="og:description" content="R9 description"' in page
    assert "data:image/png;base64,c3ludGhldGljLXRlc3QtaW1hZ2U=" in page
    assert "CPIV_INTERACTIVE_WIDGET" not in page
    assert 'id="cpiv-noise-ranking"' in page
    assert '<noscript>' in page
    assert 'value="0" aria-valuetext="0.00 pp"' in page
    assert 'class="title" lang="en"' in page
