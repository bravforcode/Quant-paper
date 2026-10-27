"""Render the JCF submission package from the templates and the run outputs.

The manuscript prose lives in templates whose numeric slots are ``{{key}}``
placeholders. The slots are filled from
:func:`research.cpiv.measurement.manuscript.build_context`, which reads only
the artefacts a run produced. A slot with no value is a build error, and a
number that does not appear in the outputs cannot reach the prose.

The package follows the publisher's compilation order and file rules:

* ``manuscript_jcf_draft.md`` — the anonymised manuscript (figure and table
  legends, abstract, keywords, key messages, title, main text, declarations,
  references);
* ``manuscript_jcf_supplement.md`` — the appendices and Table S1, which the
  publisher does not typeset with the article;
* ``submission/title_page.md`` — the separate title page, carrying the short
  title, the word count and the figure and table count;
* ``submission/tables/table_N.csv`` — each table as a separate editable file.

The build refuses to finish if the rendered manuscript breaks one of the
journal's stated limits (see :mod:`research.cpiv.measurement.manuscript_limits`).

Usage::

    .venv/Scripts/python.exe -m research.cpiv.measurement.build_manuscript
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from research.cpiv.measurement.manuscript import (
    BenchmarkOutputs,
    build_context,
)
from research.cpiv.measurement.manuscript_limits import check, words

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
DOCS = REPO_ROOT / "docs" / "cpiv-jcf"
TEMPLATE = DOCS / "manuscript" / "manuscript_jcf_draft.template.md"
OUTPUT = DOCS / "manuscript" / "manuscript_jcf_draft.md"
SUPPLEMENT_TEMPLATE = DOCS / "manuscript" / "manuscript_jcf_supplement.template.md"
SUPPLEMENT_OUTPUT = DOCS / "manuscript" / "manuscript_jcf_supplement.md"
SUBMISSION = DOCS / "submission"
TITLE_PAGE = SUBMISSION / "title_page.md"
TABLE_DIR = SUBMISSION / "tables"

TITLE = (
    "When Is a Call–Put Implied-Volatility Spread Measurable? "
    "An Abstention-Aware Protocol Validated Against a Known Truth"
)
SHORT_TITLE = "When Is a CPIV Measurable?"
AUTHOR = "Phirawit Jitnarong"

SLOT = re.compile(r"\{\{([A-Za-z0-9_.]+)\}\}")


def render(template: str, context: dict[str, str]) -> str:
    """Fill every ``{{key}}`` slot; an unknown key is an error."""
    missing: list[str] = []

    def substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            missing.append(key)
            return match.group(0)
        return context[key]

    rendered = SLOT.sub(substitute, template)
    if missing:
        unknown = ", ".join(sorted(set(missing)))
        raise KeyError(f"manuscript template has unfilled slots: {unknown}")
    return rendered


def _main_text(rendered: str) -> str:
    lines = rendered.split("\n")
    start = end = None
    for index, line in enumerate(lines):
        if start is None and re.match(r"^##\s+1\.\s", line):
            start = index
        elif start is not None and re.match(r"^##\s+Declarations of Interest", line):
            end = index
            break
    return "\n".join(lines[start:end]) if start is not None else ""


def _abstract(rendered: str) -> str:
    match = re.search(r"## Abstract\n(.*?)\n## Keywords", rendered, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def _tables(rendered: str) -> list[tuple[int, str, list[list[str]]]]:
    """Every ``**Table N.**`` caption with the markdown table under it."""
    tables: list[tuple[int, str, list[list[str]]]] = []
    lines = rendered.split("\n")
    index = 0
    while index < len(lines):
        match = re.match(r"^\*\*Table (\d+)\.\s*(.+)\*\*\s*$", lines[index])
        if not match:
            index += 1
            continue
        number = int(match.group(1))
        caption_parts = [match.group(2).strip()]
        index += 1
        while (
            index < len(lines)
            and lines[index].strip()
            and not lines[index].lstrip().startswith("|")
        ):
            caption_parts.append(lines[index].strip())
            index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1
        rows: list[list[str]] = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
                rows.append(cells)
            index += 1
        # A caption with no table under it is a legend entry, not a table.
        if rows:
            tables.append((number, " ".join(caption_parts), rows))
    return tables


def write_table_csvs(rendered: str, directory: Path) -> list[Path]:
    """Write each main-text table as a separate editable CSV."""
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for number, _, rows in _tables(rendered):
        path = directory / f"table_{number}.csv"
        header, body = rows[0], rows[1:]
        width = len(header)
        lines = [",".join(_csv_cell(cell) for cell in header)]
        for row in body:
            padded = row + [""] * (width - len(row))
            lines.append(",".join(_csv_cell(cell) for cell in padded[:width]))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _csv_cell(cell: str) -> str:
    plain = cell.replace("**", "").replace("*", "").strip()
    if any(character in plain for character in ',"'):
        return '"' + plain.replace('"', '""') + '"'
    return plain


def _figure_paths(rendered: str) -> list[Path]:
    return [Path(target) for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", rendered)]


def title_page(rendered: str) -> str:
    """The separate title page the publisher requires."""
    tables = _tables(rendered)
    figures = _figure_paths(rendered)
    main_words = words(_main_text(rendered))
    abstract_words = words(_abstract(rendered))
    figure_sentence = (
        "One figure" if len(figures) == 1 else f"{len(figures)} figures"
    ) if figures else "No figures"
    return f"""# Title page

**Title.** {TITLE}

**Author.** {AUTHOR}

**Affiliation.** คณะวิทยาการสารสนเทศ สาขาวิทยาการคอมพิวเตอร์, Burapha University, Chonburi, Thailand

**Postal address.** 169 Long-Had Bangsaen Road, Saen Suk, Mueang
Chonburi, Chonburi 20131, Thailand

**Email.** nxme176@gmail.com

**Corresponding author.** {AUTHOR}, nxme176@gmail.com

**Running header (short title).** {SHORT_TITLE}

**Number of words.** Main text {main_words:,} words, abstract
{abstract_words} words, excluding references, declarations and the
supplementary material.

**Number of figures and tables.** {figure_sentence}; {len(tables)} tables in
the main text, and two further tables (Tables S1 and S2) in the
supplementary material.

**Supplementary material.** Appendices A and B, Table S1, and one CSV file
per main-text table, supplied as separate editable files.
"""


def build(
    template_path: Path = TEMPLATE,
    output_path: Path = OUTPUT,
    study_dir: Path | None = None,
    sweep_dir: Path | None = None,
    supplement_path: Path = SUPPLEMENT_TEMPLATE,
    supplement_output: Path = SUPPLEMENT_OUTPUT,
    strict: bool = True,
) -> str:
    """Render the manuscript and the rest of the package; return the text."""
    outputs = BenchmarkOutputs.load(
        study_dir or study_dir_default(), sweep_dir or sweep_dir_default()
    )
    context = build_context(outputs)
    template = template_path.read_text(encoding="utf-8")
    rendered = render(template, context)

    report = check(rendered)
    if strict and not report.ok:
        raise SystemExit(
            f"{output_path} breaks a submission limit:\n{report.summary()}"
        )

    # An embedded figure that is not on disk would reach the DOCX as a broken
    # link, so the build checks before it writes anything.
    for figure in _figure_paths(rendered):
        # The path is authored in the template, so it is relative to that file.
        resolved = template_path.parent / figure
        if not resolved.exists():
            raise SystemExit(
                f"{output_path} embeds {figure}, which does not exist; run "
                "research.cpiv.measurement.figure_frontier first"
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    supplement_template = supplement_path.read_text(encoding="utf-8")
    supplement = render(supplement_template, context)
    supplement_output.write_text(supplement, encoding="utf-8")

    TITLE_PAGE.parent.mkdir(parents=True, exist_ok=True)
    TITLE_PAGE.write_text(title_page(rendered), encoding="utf-8")
    write_table_csvs(rendered, TABLE_DIR)
    return rendered


def study_dir_default() -> Path:
    return HERE / "outputs" / "study"


def sweep_dir_default() -> Path:
    return HERE / "outputs" / "sweep"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    rendered = build(args.template, args.output)
    tables = len(_tables(rendered))
    print(f"wrote {args.output} ({words(_main_text(rendered))} main-text words)")
    print(f"wrote {SUPPLEMENT_OUTPUT}")
    print(f"wrote {TITLE_PAGE} and {tables} table CSVs in {TABLE_DIR}")
    print(check(rendered).summary())


if __name__ == "__main__":
    main()
