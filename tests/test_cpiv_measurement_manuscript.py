"""The manuscript package must stay inside the journal's stated limits.

These tests render the manuscript from the run artefacts, then measure it the
way the publisher's submission guidelines measure it. They also check that the
prose cannot drift away from the data: the abstention split has to sum to the
attempted count, the derived ratios have to be the ones the outputs imply, and
the anonymised document must not carry the author's name.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from research.cpiv.measurement.manuscript import BenchmarkOutputs, build_context
from research.cpiv.measurement.manuscript_limits import (
    AUTHOR_NAME,
    MAX_KEY_MESSAGE_CHARS,
    MAX_MAIN_TEXT_WORDS,
    check,
    words,
)

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_DIR = ROOT / "docs" / "cpiv-jcf" / "manuscript"
STUDY_DIR = ROOT / "research" / "cpiv" / "measurement" / "outputs" / "study"
SWEEP_DIR = ROOT / "research" / "cpiv" / "measurement" / "outputs" / "sweep"

pytestmark = pytest.mark.skipif(
    not (STUDY_DIR / "study_summary.json").exists()
    or not (SWEEP_DIR / "verdict.json").exists(),
    reason="the run artefacts the manuscript is rendered from are not present",
)


def _rendered() -> str:
    from research.cpiv.measurement.build_manuscript import render

    outputs = BenchmarkOutputs.load(STUDY_DIR, SWEEP_DIR)
    template = (MANUSCRIPT_DIR / "manuscript_jcf_draft.template.md").read_text(
        encoding="utf-8"
    )
    return render(template, build_context(outputs))


def _context() -> dict[str, str]:
    return build_context(BenchmarkOutputs.load(STUDY_DIR, SWEEP_DIR))


def test_the_rendered_manuscript_meets_every_submission_limit() -> None:
    report = check(_rendered())
    assert report.ok, report.summary()
    assert report.main_text_words <= MAX_MAIN_TEXT_WORDS
    assert 150 <= report.abstract_words <= 200
    assert report.abstract_paragraphs == 1
    assert 4 <= report.keywords <= 6
    assert 3 <= report.key_messages <= 4


def test_the_abstract_states_the_benchmark_scope_and_the_failed_rule() -> None:
    rendered = _rendered()
    abstract = rendered.split("## Abstract")[1].split("## Keywords")[0]
    assert "synthetic" in abstract
    assert "Five of the six declared rules pass" in " ".join(abstract.split())
    assert "R3, coverage stability across market specifications, fails" in " ".join(
        abstract.split()
    )


def test_the_tally_reports_r3_as_failed_and_r6_as_passed_on_the_replication_seeds() -> None:
    rendered = _rendered()
    assert re.search(r"\| R3 \|.*\bFAIL\b", rendered)
    assert re.search(r"\| R6 \|.*\bPASS\b", rendered)
    assert re.search(r"\| R1 \|.*\bPASS\b", rendered)
    assert "NOT EVALUATED" not in rendered


def test_the_document_lists_legends_before_the_abstract() -> None:
    rendered = _rendered()
    assert rendered.index("## Figure and table legends") < rendered.index("## Abstract")
    assert rendered.index("## Key messages") < rendered.index("# When Is a Call")


def test_no_numbered_table_is_captioned_without_being_discussed() -> None:
    rendered = _rendered()
    body = rendered.split("## 1. Introduction", 1)[1]
    prose = "\n".join(
        line
        for line in body.split("\n")
        if not line.lstrip().startswith("|") and not line.lstrip().startswith("**Table ")
    )
    for number in re.findall(r"^\*\*Table (\d+)\.", body, flags=re.MULTILINE):
        assert re.search(rf"\bTable {number}\b", prose), f"Table {number} is never cited"


def test_every_reference_is_cited_and_every_citation_has_a_reference() -> None:
    rendered = _rendered()
    references = rendered.split("## References", 1)[1]
    surnames = re.findall(r"^([A-Z][A-Za-z'\-\u00C0-\u024F]+),", references, flags=re.MULTILINE)
    body = rendered.split("## 1. Introduction", 1)[1].split("## References", 1)[0]
    assert surnames, "the reference list is empty"
    for surname in surnames:
        assert surname in body, f"{surname} is in the list but never cited"


def test_the_abstention_split_sums_to_the_attempted_count() -> None:
    context = _context()
    total = int(context["study.abstained.total"].replace(",", ""))
    certified = int(context["study.tolerance.certified"].replace(",", ""))
    attempted = int(context["study.attempted"].replace(",", ""))
    assert total + certified == attempted

    outside = int(context["study.tolerance.outside"].replace(",", ""))
    partial = int(context["study.terminal.partially_resolved"].replace(",", ""))
    earlier = int(context["study.abstained.earlier"].replace(",", ""))
    assert outside + partial + earlier == total


def test_the_hand_typed_ratios_are_the_ones_the_outputs_imply() -> None:
    context = _context()
    # 60-odd, not "sixty" typed by hand: the slot is the rounded ratio.
    assert context["study.error.raw_over_certified"] == "61"
    # The spot and rate perturbations move the CPIV several times the certified
    # error, so the prose may not call it an order of magnitude.
    assert int(context["study.perturbation.spot_shift_1bp.over_certified_error"]) >= 5
    assert int(context["study.perturbation.rate_shift_5bp.over_certified_error"]) >= 5
    rendered = _rendered()
    assert "order of magnitude larger than the certified subset" not in rendered


def test_the_p_value_floor_is_reported_as_a_floor() -> None:
    context = _context()
    assert context["sweep.frontier_p_floor"] == "0.0005"
    assert "floor of the test" in _rendered()


def test_the_anonymised_manuscript_does_not_name_the_author() -> None:
    assert AUTHOR_NAME not in _rendered()


def test_an_uncited_reference_is_a_violation() -> None:
    text = _rendered().replace("White, H. (2000)", "Whitcombe, H. (2000)")
    assert any("Whitcombe" in violation for violation in check(text).violations)


def test_an_overlong_key_message_is_a_violation() -> None:
    rendered = _rendered()
    long_message = "- " + "x" * (MAX_KEY_MESSAGE_CHARS + 1)
    broken = rendered.replace(
        "- Abstention selects a genuinely easier set, not merely a smaller one",
        long_message,
    )
    assert any("key message" in violation for violation in check(broken).violations)


def test_a_missing_legend_is_a_violation() -> None:
    rendered = _rendered()
    broken = rendered.replace("**Table 3.** The selection frontier", "**Table 9.** The frontier")
    violations = check(broken).violations
    assert any("Table 3 has no entry" in violation for violation in violations)


def test_a_figure_without_a_legend_is_a_violation() -> None:
    rendered = _rendered()
    broken = rendered.replace("**Figure 1.** Two panels", "**Figure 2.** Two panels")
    assert any(
        "Figure 1 has no entry" in violation for violation in check(broken).violations
    )


def test_a_table_row_that_disagrees_with_its_header_is_a_violation() -> None:
    rendered = _rendered()
    broken = rendered.replace(
        "|--:|--:|--:|--:|--:|--:|--:|--:|--:|\n| 0.075",
        "|--:|--:|--:|--:|--:|--:|--:|--:|\n| 0.075",
    )
    assert any("cells against" in violation for violation in check(broken).violations)


def test_the_supplement_carries_the_two_supplementary_tables() -> None:
    from research.cpiv.measurement.build_manuscript import render

    template = (MANUSCRIPT_DIR / "manuscript_jcf_supplement.template.md").read_text(
        encoding="utf-8"
    )
    supplement = render(template, _context())
    assert "## Table S1." in supplement
    assert "## Table S2." in supplement
    assert "| Family | Bucket | n |" in supplement
    assert "{{" not in supplement


def test_the_package_writes_a_title_page_with_the_required_fields(tmp_path: Path) -> None:
    from research.cpiv.measurement import build_manuscript as builder

    main = tmp_path / "manuscript.md"
    supplement = tmp_path / "supplement.md"
    title_page = tmp_path / "title_page.md"
    tables = tmp_path / "tables"
    originals = (builder.TITLE_PAGE, builder.TABLE_DIR)
    builder.TITLE_PAGE, builder.TABLE_DIR = title_page, tables
    try:
        builder.build(
            output_path=main,
            supplement_output=supplement,
            study_dir=STUDY_DIR,
            sweep_dir=SWEEP_DIR,
        )
    finally:
        builder.TITLE_PAGE, builder.TABLE_DIR = originals

    page = title_page.read_text(encoding="utf-8")
    assert "Running header (short title).** When Is a CPIV Measurable?" in page
    short_title = page.split("**Running header (short title).**")[1].split("\n")[0].strip()
    assert len(short_title) <= 50
    assert "Number of words" in page
    assert "Number of figures and tables" in page
    assert "One figure; 7 tables" in page
    assert len(list(tables.glob("table_*.csv"))) == 7
    assert words(Path(main).read_text(encoding="utf-8")) > 0
