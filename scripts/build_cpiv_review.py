"""Build the CPIV review as standalone HTML, DOCX, and PDF."""

from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "cpiv" / "manuscript_r8.md"
REFERENCE_DOCX = ROOT / "dist" / "cpiv" / "reference.docx"
GENERATED = ROOT / "research" / "cpiv" / "generated" / "revision_20261008_r8"
DEFAULT_REVISION = "r8"
DEFAULT_OUTPUT = ROOT / "dist" / "cpiv" / f"review-{DEFAULT_REVISION}-2026-10-08"
WIDGET_MARKER = "<!-- CPIV_INTERACTIVE_WIDGET -->"
HTML_TITLE = "Call-Put Implied Volatility Spread (CPIV): What Does the Wedge Tell Us?"
HTML_DESCRIPTION = (
    "A quantitative explainer of CPIV mechanisms, model sensitivity, and "
    "reproducible synthetic quote-noise experiments."
)
WIDGET_NOISE_LEVELS = (0.0, 0.10, 0.20, 0.35, 0.50, 1.0, 2.0)


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def resolve_source_path(revision: str, source: Path | None) -> Path:
    if source is None:
        if revision != DEFAULT_REVISION:
            raise ValueError(
                "--revision only controls artifact naming; pass --source explicitly "
                "for non-default revisions"
            )
        candidate = SOURCE
    else:
        candidate = source
    return candidate if candidate.is_absolute() else ROOT / candidate


def docx_args_without_toc(common_args: list[str]) -> list[str]:
    """Avoid emitting an empty Word TOC field; HTML and PDF retain their TOCs."""
    return [
        argument
        for argument in common_args
        if argument != "--toc" and not argument.startswith("--toc-depth=")
    ]


def add_table_borders(docx_path: Path) -> None:
    borders = (
        b'<w:tblBorders>'
        b'<w:top w:val="single" w:sz="4" w:space="0" w:color="AEBBC8"/>'
        b'<w:left w:val="single" w:sz="4" w:space="0" w:color="AEBBC8"/>'
        b'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="AEBBC8"/>'
        b'<w:right w:val="single" w:sz="4" w:space="0" w:color="AEBBC8"/>'
        b'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D6DDE5"/>'
        b'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="D6DDE5"/>'
        b'</w:tblBorders>'
    )
    props_pattern = re.compile(rb'(<w:tblPr\b[^>]*>)(.*?)(</w:tblPr>)', re.DOTALL)

    with zipfile.ZipFile(docx_path) as source:
        entries = [(item, source.read(item.filename)) for item in source.infolist()]
        document_xml = next(
            payload for item, payload in entries if item.filename == "word/document.xml"
        )
        table_count = len(re.findall(rb'<w:tbl(?:\s|>)', document_xml))
        added = 0

        def patch_properties(match: re.Match[bytes]) -> bytes:
            nonlocal added
            properties = match.group(2)
            if b"<w:tblBorders" in properties:
                return match.group(0)
            # CT_TblPr orders tblBorders before tblLayout/tblCellMar/tblLook.
            # Pandoc's reference DOCX may already contain tblLayout, so inserting
            # before tblLook alone can produce invalid WordprocessingML.
            later_properties = (
                b"<w:shd",
                b"<w:tblLayout",
                b"<w:tblCellMar",
                b"<w:tblLook",
                b"<w:tblCaption",
                b"<w:tblDescription",
            )
            positions = [
                position
                for tag in later_properties
                if (position := properties.find(tag)) >= 0
            ]
            insert_at = min(positions) if positions else len(properties)
            added += 1
            properties = properties[:insert_at] + borders + properties[insert_at:]
            return match.group(1) + properties + match.group(3)

        updated_xml, property_count = props_pattern.subn(patch_properties, document_xml)
        if table_count == 0 or property_count != table_count:
            raise ValueError("could not match every DOCX table with table properties")
        if updated_xml.count(b"<w:tblBorders") != table_count:
            raise ValueError("not every DOCX table has explicit border definitions")
        if added == 0:
            return

        with tempfile.NamedTemporaryFile(
            prefix=f"{docx_path.stem}-", suffix=".tmp", dir=docx_path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w") as destination:
            for item, payload in entries:
                if item.filename == "word/document.xml":
                    payload = updated_xml
                destination.writestr(item, payload)
        os.replace(temporary_path, docx_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def patch_docx_figure_captions_and_wide_table_pagebreaks(
    docx_path: Path, expected_figure_count: int | None = None
) -> None:
    """Prefix figure captions and start diagnostic-table captions on fresh pages."""
    paragraph_pattern = re.compile(rb'<w:p(?:\s[^>]*)?>.*?</w:p>', re.DOTALL)
    text_pattern = re.compile(rb'<w:t\b[^>]*>(.*?)</w:t>', re.DOTALL)
    prefix_pattern = re.compile(r"^\s*Figure\s+\d+\s*[:.]\s*", re.IGNORECASE)
    figure_count = 0
    table5_count = 0
    table6_count = 0
    table7_count = 0
    table10_count = 0

    with zipfile.ZipFile(docx_path) as source:
        entries = [(item, source.read(item.filename)) for item in source.infolist()]
    document_xml = next(
        payload for item, payload in entries if item.filename == "word/document.xml"
    )

    def patch_paragraph(match: re.Match[bytes]) -> bytes:
        nonlocal figure_count, table5_count, table6_count, table7_count, table10_count
        paragraph = match.group(0)
        text_nodes = list(text_pattern.finditer(paragraph))
        plain_text = html.unescape(
            "".join(node.group(1).decode("utf-8") for node in text_nodes)
        )
        if b'w:pStyle w:val="ImageCaption"' in paragraph:
            figure_count += 1
            if not text_nodes:
                raise ValueError("figure caption paragraph has no text node")
            number = f"Figure {figure_count}: "
            first = text_nodes[0]
            first_text = html.unescape(first.group(1).decode("utf-8"))
            existing = prefix_pattern.match(first_text)
            content = first_text[existing.end():] if existing else first_text
            replacement = number.encode("ascii") + html.escape(
                content, quote=False
            ).encode("utf-8")
            paragraph = (
                paragraph[:first.start(1)]
                + replacement
                + paragraph[first.end(1):]
            )

        if plain_text.startswith("Table 5."):
            table5_count += 1
        elif plain_text.startswith("Table 6."):
            table6_count += 1
        elif plain_text.startswith("Table 7."):
            table7_count += 1
        elif plain_text.startswith("Table 10."):
            table10_count += 1

        needs_page_break = (
            plain_text.startswith("Table 5.")
            or plain_text.startswith("Table 6.")
            or plain_text.startswith("Table 7.")
            or plain_text.startswith("The proposed staged checklist")
        )
        if needs_page_break and b"<w:pageBreakBefore" not in paragraph:
            ppr = re.search(
                rb"<w:pPr(?:\s[^>]*)?>(.*?)</w:pPr>", paragraph, re.DOTALL
            )
            if ppr:
                ppr_content = ppr.group(1)
                style_match = re.search(rb"<w:pStyle\b[^>]*/>", ppr_content)
                insertion = ppr.start(1) + (style_match.end() if style_match else 0)
                paragraph = (
                    paragraph[:insertion]
                    + b"<w:pageBreakBefore/>"
                    + paragraph[insertion:]
                )
            else:
                opening = re.match(rb"<w:p(?:\s[^>]*)?>", paragraph)
                if opening is None:
                    raise ValueError("could not locate wide-table caption paragraph")
                paragraph = (
                    paragraph[:opening.end()]
                    + b"<w:pPr><w:pageBreakBefore/></w:pPr>"
                    + paragraph[opening.end():]
                )
        return paragraph

    updated_xml = paragraph_pattern.sub(patch_paragraph, document_xml)
    if expected_figure_count is not None and figure_count != expected_figure_count:
        raise ValueError(
            f"expected {expected_figure_count} Word figure captions, found {figure_count}"
        )
    if figure_count == 0:
        raise ValueError("expected at least one Word figure caption")
    if table5_count != 1:
        raise ValueError(f"expected one Table 5 caption, found {table5_count}")
    if table6_count != 1:
        raise ValueError(f"expected one Table 6 caption, found {table6_count}")
    if table7_count != 1:
        raise ValueError(f"expected one Table 7 caption, found {table7_count}")
    if table10_count != 1:
        raise ValueError(f"expected one Table 10 caption, found {table10_count}")
    with tempfile.NamedTemporaryFile(
        prefix=f"{docx_path.stem}-layout-", suffix=".tmp", dir=docx_path.parent,
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w") as destination:
            for item, payload in entries:
                if item.filename == "word/document.xml":
                    payload = updated_xml
                destination.writestr(item, payload)
        os.replace(temporary_path, docx_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def number_html_figure_captions(page: str) -> str:
    caption_pattern = re.compile(
        r"(<figcaption\b[^>]*>)(.*?)(</figcaption>)", re.DOTALL | re.IGNORECASE
    )
    figure_count = 0

    def number_caption(match: re.Match[str]) -> str:
        nonlocal figure_count
        figure_count += 1
        caption = prefix_pattern.sub("", match.group(2), count=1)
        return f"{match.group(1)}Figure {figure_count}: {caption}{match.group(3)}"

    prefix_pattern = re.compile(r"^\s*Figure\s+\d+\s*[:.]\s*", re.IGNORECASE)
    page = caption_pattern.sub(number_caption, page)
    return page


def prepare_r22_pdf_source_text(source_text: str) -> str:
    """Keep the American figure and wide diagnostic tables with their content."""
    table10_marker = "**Table 10.**"
    table3_marker = "**Table 3.**"
    section8_marker = "## 8. Interpretation and limits"
    protocol_lead_marker = (
        "The proposed staged checklist for future paired-option work is summarized in Table 10."
    )
    american_figure_marker = (
        "![CRR and equal-probability Jarrow–Rudd American-put synthetic tree comparison.]"
    )
    if source_text.count(table10_marker) != 1:
        raise ValueError("R22 source must contain exactly one Table 10 caption")
    if source_text.count(table3_marker) != 1:
        raise ValueError("R22 source must contain exactly one Table 3 caption")
    if source_text.count(section8_marker) != 1:
        raise ValueError("R22 source must contain exactly one Section 8 heading")
    if source_text.count(protocol_lead_marker) != 1:
        raise ValueError("R22 source must contain exactly one Table 10 lead paragraph")
    if source_text.index(table10_marker) < source_text.index(section8_marker):
        raise ValueError("R22 protocol Table 10 must appear within Section 8")
    if source_text.index(protocol_lead_marker) < source_text.index(section8_marker):
        raise ValueError("R22 protocol lead must appear within Section 8")
    if source_text.count(american_figure_marker) != 1:
        raise ValueError("R22 source must contain exactly one American-tree figure")
    source_text = source_text.replace(
        american_figure_marker, "\\newpage\n\n" + american_figure_marker, 1
    )
    source_text = source_text.replace(
        table3_marker, "\\newpage\n\n" + table3_marker, 1
    )
    source_text = source_text.replace(
        protocol_lead_marker,
        "\\newpage\n\n" + protocol_lead_marker,
        1,
    )
    return source_text.replace(
        section8_marker, "\\newpage\n\n" + section8_marker, 1
    )


def load_noise_results(path: Path, replicates: int) -> list[dict[str, Any]]:
    results = json.loads(path.read_text(encoding="utf-8"))
    if results.get("status") != "synthetic_sensitivity_analysis_only":
        raise ValueError("stress results are not labeled as synthetic")
    if results.get("market_data_used") is not False:
        raise ValueError("stress results unexpectedly report market data")
    noise = results["quote_noise_ranking"]
    if noise.get("seed") != 20261008 or noise.get("replicates") != replicates:
        raise ValueError("stress-result seed or replication count does not match")
    rows = noise["results"]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("stress results must contain a list of result objects")
    if not rows or any("example_ranked_names" not in row for row in rows):
        raise ValueError("stress results must contain a representative ranked sample")
    levels = tuple(float(row["target_cpiv_noise_sd_pp"]) for row in rows)
    if levels != WIDGET_NOISE_LEVELS:
        raise ValueError("widget data must contain the seven declared noise levels")
    quantile_fields = (
        "rank_inversions_p05",
        "rank_inversions_median",
        "rank_inversions_p95",
        "spearman_rho_p05",
        "spearman_rho_median",
        "spearman_rho_p95",
    )
    for row in rows:
        sample = row["example_ranked_names"]
        symbols = [str(item["symbol"]) for item in sample]
        if len(sample) != 10 or len(set(symbols)) != 10:
            raise ValueError("each widget example must contain ten unique names")
        if any(field not in row for field in quantile_fields):
            raise ValueError("stress results are missing Monte Carlo quantiles")
    return cast(list[dict[str, Any]], rows)


def _sample_order(row: dict[str, Any]) -> list[str]:
    sample = row["example_ranked_names"]
    return [
        str(item["symbol"])
        for item in sorted(sample, key=lambda item: int(item["rank_low_to_high"]))
    ]


def _example_metrics(
    row: dict[str, Any], baseline: dict[str, Any]
) -> dict[str, float | int | bool]:
    baseline_order = _sample_order(baseline)
    sample_order = _sample_order(row)
    if (
        len(sample_order) != len(baseline_order)
        or set(sample_order) != set(baseline_order)
    ):
        raise ValueError("example and zero-noise baseline must contain the same names")

    baseline_rank = {name: rank for rank, name in enumerate(baseline_order)}
    sample_ranks = [baseline_rank[name] for name in sample_order]
    inversions = sum(
        sample_ranks[left] > sample_ranks[right]
        for left in range(len(sample_ranks))
        for right in range(left + 1, len(sample_ranks))
    )
    sample_rank = {name: rank for rank, name in enumerate(sample_order)}
    squared_rank_difference = sum(
        (sample_rank[name] - baseline_rank[name]) ** 2 for name in baseline_order
    )
    count = len(baseline_order)
    rho = 1.0 - 6.0 * squared_rank_difference / (count * (count**2 - 1))
    tail_size = max(1, count // 5)
    changed_membership = (
        set(sample_order[:tail_size]) != set(baseline_order[:tail_size])
        or set(sample_order[-tail_size:]) != set(baseline_order[-tail_size:])
    )
    return {
        "inversions": int(inversions),
        "spearman_rho": rho,
        "extreme_membership_changed": changed_membership,
    }


def _format_count(value: float) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.1f}"


def _rank_list_html(sample: list[dict[str, Any]], axis_limit: float) -> str:
    rows: list[str] = []
    for item in sorted(sample, key=lambda entry: int(entry["rank_low_to_high"])):
        value = float(item["cpiv_pp"])
        width = min(50.0, 50.0 * abs(value) / axis_limit)
        side = "right" if value < 0 else "left"
        direction = "negative" if value < 0 else "positive"
        label = html.escape(
            f"{int(item['rank_low_to_high'])}. {item['symbol']} · {value:.2f} pp"
        )
        rows.append(
            '<li class="rank-row">'
            f'<span class="rank-label">{label}</span>'
            '<span class="rank-meter" aria-hidden="true">'
            '<span class="rank-zero"></span>'
            f'<span class="rank-fill {direction}" '
            f'style="{side}:50%;width:{width:.2f}%"></span>'
            '</span></li>'
        )
    return "\n".join(rows)


def _rank_axis_html(axis_limit: float) -> str:
    ticks = (-axis_limit, -axis_limit / 2, 0.0, axis_limit / 2, axis_limit)
    labels: list[str] = []
    for index, value in enumerate(ticks):
        left = index * 25
        if value == 0:
            label = "0"
        else:
            sign = "−" if value < 0 else "+"
            label = f"{sign}{abs(value):.1f}"
        labels.append(f'<span style="left:{left}%">{label}</span>')
    return (
        '<div class="rank-axis" aria-hidden="true">'
        '<span></span><div class="rank-axis-ticks">'
        + "".join(labels)
        + "</div></div>"
    )


def _monte_carlo_summary_html(row: dict[str, Any]) -> str:
    rho = (
        f"ρ median {float(row['spearman_rho_median']):.3f} "
        f"(p05–p95 {float(row['spearman_rho_p05']):.3f}–"
        f"{float(row['spearman_rho_p95']):.3f})"
    )
    inversions = (
        f"pairwise inversions median {_format_count(row['rank_inversions_median'])} "
        f"(p05–p95 {_format_count(row['rank_inversions_p05'])}–"
        f"{_format_count(row['rank_inversions_p95'])})"
    )
    return (
        f"Across {int(row['replicates']):,} Monte Carlo replicates: {rho}; "
        f"{inversions}; P(no inversion) "
        f"{100 * float(row['probability_no_pairwise_inversions']):.2f}%; "
        f"P(extreme-quintile crossover) "
        f"{100 * float(row['probability_any_extreme_quintile_crossover']):.2f}%; "
        f"P(low/high 20% membership change) "
        f"{100 * float(row['probability_long_short_membership_change']):.2f}%."
    )


def _example_summary_text(
    row: dict[str, Any], baseline: dict[str, Any]
) -> str:
    metrics = _example_metrics(row, baseline)
    membership = (
        "changed" if metrics["extreme_membership_changed"] else "unchanged"
    )
    return (
        "One stored example draw, compared with the zero-noise baseline: "
        f"{metrics['inversions']} pairwise inversion(s); "
        f"Spearman ρ {float(metrics['spearman_rho']):.3f}; "
        f"low/high 20% membership {membership}. This is one realization, "
        "not a Monte Carlo average."
    )


def interactive_widget(rows: list[dict[str, Any]]) -> str:
    if not rows:
        raise ValueError("interactive widget requires at least one result row")
    data = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")
    default_index = next(
        (
            index
            for index, row in enumerate(rows)
            if abs(float(row["target_cpiv_noise_sd_pp"]) - 0.20) < 1e-12
        ),
        min(2, len(rows) - 1),
    )
    baseline = next(
        (
            row
            for row in rows
            if abs(float(row["target_cpiv_noise_sd_pp"])) < 1e-12
        ),
        rows[0],
    )
    baseline_data = json.dumps(baseline, ensure_ascii=False, separators=(",", ":"))
    baseline_data = baseline_data.replace("</", "<\\/")
    all_values = [
        abs(float(item["cpiv_pp"]))
        for row in rows
        for item in row["example_ranked_names"]
    ]
    axis_limit = max(0.1, math.ceil(max(all_values, default=0.0) * 10) / 10)
    default_row = rows[default_index]
    tick_labels = "".join(
        '<span class="noise-level-label{}">{:.2f}</span>'.format(
            " is-current" if index == default_index else "",
            float(row["target_cpiv_noise_sd_pp"]),
        )
        for index, row in enumerate(rows)
    )
    script = """
<section class="interactive-widget" role="group" aria-label="ตัวสำรวจผล quote-noise"
  data-axis-limit-pp="__LIMIT__">
  <p><strong>ตัวอย่างอันดับ CPIV ในข้อมูลสังเคราะห์ 10 ชื่อ (ภาพประกอบแบบ fixed-seed)</strong></p>
  <label for="cpiv-noise-range">ระดับ SD เป้าหมายของ CPIV measurement noise (pp)</label>
  <div class="noise-slider">
    <input id="cpiv-noise-range" type="range" min="0" max="__MAX__" step="1"
      value="__DEFAULT__" aria-valuetext="__DEFAULT_LEVEL__ pp"
      aria-describedby="cpiv-noise-help">
    <div id="cpiv-noise-level-labels" class="noise-level-labels" aria-hidden="true">
      __TICKS__
    </div>
  </div>
  <output id="cpiv-noise-output" for="cpiv-noise-range" aria-live="polite">
    Selected discrete noise SD: __DEFAULT_LEVEL__ pp.
  </output>
  <p class="widget-note" id="cpiv-noise-help">
    จุดเลื่อนแทนระดับจำลอง 7 ค่าแบบไม่ห่างเท่ากัน; เลือกแถวผลที่บันทึกไว้
    ไม่ได้คำนวณราคา/IV ใหม่หรือรัน Monte Carlo ในเบราว์เซอร์.
    แท่งใช้แกนสมมาตรเดียวกันทุกระดับ; ค่าเป็น pp และเป็นข้อมูลสังเคราะห์
    ไม่ใช่หลักทรัพย์จริงหรือช่วงความเชื่อมั่น.
  </p>
  <section class="widget-summary" aria-labelledby="cpiv-mc-heading">
    <h4 id="cpiv-mc-heading">Monte Carlo summary — 2,000 replicates</h4>
    <p id="cpiv-mc-summary">__MC_SUMMARY__</p>
    <p class="widget-note">
      p05–p95 คือ empirical quantiles ข้าม replicates ไม่ใช่ confidence interval.
    </p>
  </section>
  <section class="widget-summary" aria-labelledby="cpiv-example-heading">
    <h4 id="cpiv-example-heading">One stored example realization</h4>
    <p id="cpiv-example-summary">__EXAMPLE_SUMMARY__</p>
  </section>
  __AXIS__
  <ol id="cpiv-noise-ranking" class="rank-list" aria-label="อันดับ CPIV สังเคราะห์จากต่ำไปสูง">
    __RANKS__
  </ol>
  <noscript>
    <p class="widget-note">JavaScript ปิดอยู่; เนื้อหาด้านบนแสดงผลลัพธ์ที่บันทึกไว้
      ที่ระดับ __DEFAULT_LEVEL__ pp และตัวเลื่อนไม่สามารถเปลี่ยนระดับได้.</p>
  </noscript>
</section>
<script>
(() => {
  const results = __DATA__;
  const baseline = __BASELINE__;
  const widget = document.querySelector(".interactive-widget");
  const slider = document.getElementById("cpiv-noise-range");
  const output = document.getElementById("cpiv-noise-output");
  const aggregate = document.getElementById("cpiv-mc-summary");
  const exampleSummary = document.getElementById("cpiv-example-summary");
  const list = document.getElementById("cpiv-noise-ranking");
  const axisLimit = Number(widget.dataset.axisLimitPp);
  const baselineOrder = baseline.example_ranked_names
    .slice().sort((a, b) => Number(a.rank_low_to_high) - Number(b.rank_low_to_high))
    .map(item => String(item.symbol));
  function fmtCount(value) {
    const number = Number(value);
    return Number.isInteger(number) ? String(number) : number.toFixed(1);
  }
  function sampleMetrics(sample) {
    const order = sample.slice()
      .sort((a, b) => Number(a.rank_low_to_high) - Number(b.rank_low_to_high))
      .map(item => String(item.symbol));
    const baselineRank = new Map(baselineOrder.map((name, index) => [name, index]));
    const sampleRank = new Map(order.map((name, index) => [name, index]));
    const ranks = order.map(name => baselineRank.get(name));
    let inversions = 0;
    for (let left = 0; left < ranks.length; left += 1) {
      for (let right = left + 1; right < ranks.length; right += 1) {
        if (ranks[left] > ranks[right]) inversions += 1;
      }
    }
    const squaredDifferences = baselineOrder.reduce((total, name, index) => {
      const difference = sampleRank.get(name) - index;
      return total + difference * difference;
    }, 0);
    const count = order.length;
    const rho = 1 - 6 * squaredDifferences / (count * (count * count - 1));
    const tailSize = Math.max(1, Math.floor(count / 5));
    const baselineLow = new Set(baselineOrder.slice(0, tailSize));
    const baselineHigh = new Set(baselineOrder.slice(-tailSize));
    const sampleLow = new Set(order.slice(0, tailSize));
    const sampleHigh = new Set(order.slice(-tailSize));
    const sameMembers = (left, right) => left.size === right.size
      && Array.from(left).every(name => right.has(name));
    return {
      inversions,
      rho,
      membershipChanged: !sameMembers(sampleLow, baselineLow)
        || !sameMembers(sampleHigh, baselineHigh),
    };
  }
  function update() {
    const row = results[Number(slider.value)];
    const target = Number(row.target_cpiv_noise_sd_pp);
    output.textContent = "Selected discrete noise SD: " + target.toFixed(2) + " pp.";
    slider.setAttribute("aria-valuetext", target.toFixed(2) + " pp");
    document.querySelectorAll("#cpiv-noise-level-labels span").forEach((label, index) => {
      label.classList.toggle("is-current", index === Number(slider.value));
    });
    aggregate.textContent = "Across " + Number(row.replicates).toLocaleString()
      + " Monte Carlo replicates: Spearman ρ median "
      + Number(row.spearman_rho_median).toFixed(3) + " (p05–p95 "
      + Number(row.spearman_rho_p05).toFixed(3) + "–"
      + Number(row.spearman_rho_p95).toFixed(3) + "); pairwise inversions median "
      + fmtCount(row.rank_inversions_median) + " (p05–p95 "
      + fmtCount(row.rank_inversions_p05) + "–" + fmtCount(row.rank_inversions_p95)
      + "); P(no inversion) "
      + (100 * Number(row.probability_no_pairwise_inversions)).toFixed(2)
      + "%; P(extreme-quintile crossover) "
      + (100 * Number(row.probability_any_extreme_quintile_crossover)).toFixed(2)
      + "%; P(low/high 20% membership change) "
      + (100 * Number(row.probability_long_short_membership_change)).toFixed(2) + "%.";
    const sample = row.example_ranked_names;
    const metrics = sampleMetrics(sample);
    exampleSummary.textContent = "One stored example draw, compared with the "
      + "zero-noise baseline: " + metrics.inversions + " pairwise inversion(s); "
      + "Spearman ρ " + metrics.rho.toFixed(3) + "; low/high 20% membership "
      + (metrics.membershipChanged ? "changed" : "unchanged")
      + ". This is one realization, not a Monte Carlo average.";
    list.replaceChildren();
    for (const item of sample.slice().sort((a, b) =>
      Number(a.rank_low_to_high) - Number(b.rank_low_to_high))) {
      const value = Number(item.cpiv_pp);
      const entry = document.createElement("li");
      entry.className = "rank-row";
      const label = document.createElement("span");
      label.className = "rank-label";
      label.textContent = String(item.rank_low_to_high) + ". "
        + String(item.symbol) + " · " + value.toFixed(2) + " pp";
      const meter = document.createElement("span");
      meter.className = "rank-meter";
      meter.setAttribute("aria-hidden", "true");
      const zero = document.createElement("span");
      zero.className = "rank-zero";
      const bar = document.createElement("span");
      bar.className = "rank-fill " + (value < 0 ? "negative" : "positive");
      bar.style.width = Math.min(50, 50 * Math.abs(value) / axisLimit).toFixed(2) + "%";
      if (value < 0) {
        bar.style.right = "50%";
      } else {
        bar.style.left = "50%";
      }
      meter.append(zero, bar);
      entry.append(label, meter);
      list.append(entry);
    }
  }
  slider.addEventListener("input", update);
  update();
})();
</script>
"""
    return (
        script.replace("__MAX__", str(len(rows) - 1))
        .replace("__DEFAULT__", str(default_index))
        .replace("__DEFAULT_LEVEL__", f"{float(default_row['target_cpiv_noise_sd_pp']):.2f}")
        .replace("__TICKS__", tick_labels)
        .replace("__MC_SUMMARY__", html.escape(_monte_carlo_summary_html(default_row)))
        .replace(
            "__EXAMPLE_SUMMARY__",
            html.escape(_example_summary_text(default_row, baseline)),
        )
        .replace("__AXIS__", _rank_axis_html(axis_limit))
        .replace("__RANKS__", _rank_list_html(default_row["example_ranked_names"], axis_limit))
        .replace("__BASELINE__", baseline_data)
        .replace("__DATA__", data)
        .replace("__LIMIT__", f"{axis_limit:.1f}")
    )


def postprocess_html(
    path: Path,
    rows: list[dict[str, Any]],
    social_card_path: Path,
    title: str = HTML_TITLE,
    description: str = HTML_DESCRIPTION,
) -> None:
    page = path.read_text(encoding="utf-8")
    if page.count(WIDGET_MARKER) != 1:
        raise ValueError("the HTML-only interactive-widget marker must occur once")
    page = page.replace(WIDGET_MARKER, interactive_widget(rows), 1)
    page = number_html_figure_captions(page)
    if not social_card_path.is_file():
        raise FileNotFoundError(f"social-card image is missing: {social_card_path}")
    social_card = base64.b64encode(social_card_path.read_bytes()).decode("ascii")
    head_meta = "\n".join(
        [
            f'<meta property="og:title" content="{html.escape(title, quote=True)}" />',
            (
                '<meta property="og:description" content="'
                f'{html.escape(description, quote=True)}" />'
            ),
            '<meta property="og:type" content="article" />',
            '<meta name="author" content="Phirawit Jitnarong" />',
            '<meta property="og:locale" content="th_TH" />',
            '<meta property="og:locale:alternate" content="en_US" />',
            (
                '<meta property="og:image" content="data:image/png;base64,'
                f'{social_card}" />'
            ),
            (
                '<meta property="og:image:alt" content="CPIV parity-residual '
                'explainer; synthetic sensitivity analysis only" />'
            ),
        ]
    )
    if page.count("<head>") != 1:
        raise ValueError("expected exactly one HTML head element")
    charset = re.search(r'<meta\s+charset=["\'][^"\']+["\']\s*/?>', page, re.I)
    if page.lower().count("<meta") < 1 or not charset:
        raise ValueError("expected one charset declaration in the HTML head")
    head_start = page.index("<head>") + len("<head>")
    if charset.start() < head_start or charset.end() > page.index("</head>"):
        raise ValueError("HTML charset declaration must be inside the head")
    if len(re.findall(r'<meta\s+charset=', page, re.I)) != 1:
        raise ValueError("expected exactly one HTML charset declaration")
    page = page[: charset.end()] + "\n" + head_meta + page[charset.end() :]
    page, heading_count = re.subn(
        r'(<h1\b[^>]*class="title")',
        r'\1 lang="en"',
        page,
        count=1,
    )
    if heading_count != 1:
        raise ValueError("could not mark the English title heading")
    path.write_text(page, encoding="utf-8", newline="\n")
    if WIDGET_MARKER in page or "file:///" in page:
        raise ValueError("standalone HTML still contains a marker or local file URI")
    if "<math" not in page or "data:image/png;base64," not in page:
        raise ValueError("standalone HTML is missing MathML or an embedded figure")
    if page.index('charset="utf-8"') > page.index('property="og:title"'):
        raise ValueError("Open Graph tags must follow the charset declaration")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--generated", type=Path, default=GENERATED)
    parser.add_argument("--reference-doc", type=Path, default=REFERENCE_DOCX)
    parser.add_argument(
        "--refresh-docx",
        action="store_true",
        help="refresh Word contents and page-reference fields with officecli",
    )
    parser.add_argument("--artifact-date", default="2026-10-08")
    parser.add_argument("--title", default=HTML_TITLE)
    parser.add_argument("--description", default=HTML_DESCRIPTION)
    parser.add_argument("--no-toc", action="store_true",
                        help="omit the table of contents for short-form manuscripts")
    parser.add_argument("--replicates", type=int, default=2000)
    parser.add_argument(
        "--reuse-generated",
        action="store_true",
        help="reuse verified synthetic assets already in the revision folder",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"r[1-9][0-9]*", args.revision):
        parser.error("--revision must look like r3")
    if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", args.artifact_date):
        parser.error("--artifact-date must use YYYY-MM-DD")
    output = args.output or DEFAULT_OUTPUT
    output = output if output.is_absolute() else ROOT / output
    try:
        source_path = resolve_source_path(args.revision, args.source)
    except ValueError as error:
        parser.error(str(error))
    generated_path = args.generated if args.generated.is_absolute() else ROOT / args.generated
    reference_path = (
        args.reference_doc
        if args.reference_doc.is_absolute()
        else ROOT / args.reference_doc
    )
    if not source_path.is_file():
        parser.error(f"source manuscript does not exist: {source_path}")
    if not reference_path.is_file():
        parser.error(f"reference DOCX does not exist: {reference_path}")
    output.mkdir(parents=True, exist_ok=True)
    artifact_stem = f"quantcorner-cpiv-review-{args.revision}-{args.artifact_date}"
    if any(output.glob(f"{artifact_stem}.*")):
        raise FileExistsError(f"refusing to overwrite an existing deliverable in {output}")

    data_path = generated_path / "cpiv_stress_results.json"
    required_assets = [
        data_path,
        generated_path / "cpiv_carry_bias.png",
        generated_path / "cpiv_carry_bias.svg",
        generated_path / "cpiv_american_bias.png",
        generated_path / "cpiv_american_bias.svg",
        generated_path / "cpiv_quote_noise.png",
        generated_path / "cpiv_quote_noise.svg",
        generated_path / "cpiv_social_card.png",
        generated_path / "synthetic_cpiv_demo.csv",
        generated_path / "synthetic_cpiv_demo.json",
    ]
    if args.reuse_generated:
        if not all(path.is_file() for path in required_assets):
            raise FileNotFoundError("one or more revision-specific synthetic assets are missing")
        noise_rows = load_noise_results(data_path, args.replicates)
    else:
        run(
            [
                sys.executable,
                "-m",
                "research.cpiv.build_demo",
                "--output",
                str(generated_path),
                "--replicates",
                str(args.replicates),
            ]
        )
        noise_rows = load_noise_results(data_path, args.replicates)

    pandoc = shutil.which("pandoc")
    xelatex = shutil.which("xelatex")
    if not xelatex:
        miktex_xelatex = Path(
            r"C:\Users\menum\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.bat"
        )
        if miktex_xelatex.is_file():
            xelatex = str(miktex_xelatex)
    if not pandoc or not xelatex:
        raise FileNotFoundError("pandoc and xelatex must be available on PATH")

    html_path = output / f"{artifact_stem}.html"
    docx_path = output / f"{artifact_stem}.docx"
    pdf_path = output / f"{artifact_stem}.pdf"
    resource_path = os.pathsep.join(
        [str(ROOT), str(ROOT / "research" / "cpiv"), str(generated_path)]
    )
    common = [
        str(source_path),
        "--from=markdown+tex_math_dollars+tex_math_single_backslash",
        f"--resource-path={resource_path}",
    ]
    if not args.no_toc:
        common.extend(["--toc", "--toc-depth=2"])

    run(
        [
            pandoc,
            *common,
            "--to=html5",
            "--standalone",
            "--math-method=mathml",
            "--embed-resources",
            "--css=research/cpiv/style.css",
            f"--output={html_path}",
        ]
    )
    postprocess_html(
        html_path,
        noise_rows,
        generated_path / "cpiv_social_card.png",
        title=args.title,
        description=args.description,
    )

    run(
        [
            pandoc,
            *docx_args_without_toc(common),
            "--to=docx",
            f"--reference-doc={reference_path}",
            f"--output={docx_path}",
        ]
    )
    add_table_borders(docx_path)
    source_image_count = sum(
        line.lstrip().startswith("![")
        for line in source_path.read_text(encoding="utf-8").splitlines()
    )
    if "**Table 10.**" in source_path.read_text(encoding="utf-8"):
        patch_docx_figure_captions_and_wide_table_pagebreaks(
            docx_path, expected_figure_count=source_image_count
        )
    if args.refresh_docx:
        officecli = shutil.which("officecli")
        if not officecli:
            raise FileNotFoundError("officecli is required by --refresh-docx")
        run([officecli, "refresh", str(docx_path)])
        run([officecli, "close", str(docx_path)])

    pdf_source_path = source_path
    temporary_pdf_source: Path | None = None
    if args.revision == "r22":
        source_text = source_path.read_text(encoding="utf-8")
        pdf_text = prepare_r22_pdf_source_text(source_text)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".md", dir=output, delete=False
        ) as temporary:
            temporary.write(pdf_text)
            temporary_pdf_source = Path(temporary.name)
        pdf_source_path = temporary_pdf_source
    pdf_common = [str(pdf_source_path), *common[1:]]
    try:
        run(
            [
                pandoc,
                *pdf_common,
                "--to=latex",
                f"--pdf-engine={xelatex}",
                "--variable=papersize:a4",
                "--variable=geometry:margin=1in",
                "--variable=mainfont:Tahoma",
                "--variable=sansfont:Tahoma",
                "--variable=monofont:Cascadia Mono",
                "--variable=fontsize:10pt",
                "--variable=linestretch:1.15",
                "--variable=header-includes:\\usepackage{fvextra}"
                "\\RecustomVerbatimEnvironment{verbatim}{Verbatim}"
                "{breaklines,fontsize=\\footnotesize}"
                "\\RecustomVerbatimEnvironment{Highlighting}{Verbatim}"
                "{breaklines,commandchars=\\\\\\{\\},fontsize=\\footnotesize}",
                f"--output={pdf_path}",
            ]
        )
    finally:
        if temporary_pdf_source is not None:
            temporary_pdf_source.unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "html": str(html_path),
                "docx": str(docx_path),
                "pdf": str(pdf_path),
                "assets": [str(path) for path in required_assets],
                "replicates_per_noise_level": args.replicates,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
