"""Build the JCF submission package: DOCX sources, PDFs and a receipt.

The manuscript is rendered by
:mod:`research.cpiv.measurement.build_manuscript`; this script turns the
rendered Markdown into the files the publisher asks for, in the order it asks
for them:

1. a Word source file and a PDF for the anonymised manuscript;
2. the same for the separate title page;
3. the same for the supplementary material;
4. a manifest of SHA-256 hashes for the package.

The DOCX files are produced with Pandoc against a reference document whose
table style carries visible rules; the PDFs are exported from those DOCX
files with Word's own PDF export, so the PDF and the editable source are the
same document. Both tools are local; nothing is uploaded.

Usage::

    .venv/Scripts/python.exe scripts/build_jcf_submission.py
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.cpiv.measurement.build_manuscript import AUTHOR  # noqa: E402

MANUSCRIPT_DIR = ROOT / "docs" / "cpiv-jcf" / "manuscript"
SUBMISSION = ROOT / "docs" / "cpiv-jcf" / "submission"
REFERENCE = SUBMISSION / "reference.docx"

DOCUMENTS = (
    ("manuscript_jcf_draft", MANUSCRIPT_DIR / "manuscript_jcf_draft.md"),
    ("title_page", SUBMISSION / "title_page.md"),
    ("manuscript_jcf_supplement", MANUSCRIPT_DIR / "manuscript_jcf_supplement.md"),
)

#: Built for the journal upload, but kept out of the public tree and the
#: manifest: they carry the author's name and contact details.
PRIVATE_STEMS = frozenset({"title_page", "combined"})

#: Horizontal rules above, below and between rows; no vertical rules, which is
#: the usual convention for numeric tables in a journal manuscript.
_TBL_BORDERS = (
    "<w:tblBorders>"
    '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
    '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
    '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
    "</w:tblBorders>"
)

#: Numeric tables are set a point and a half below the body text so that the
#: nine-column frontier table fits across A4 without wrapping its headings.
_TBL_RUN = '<w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'


def run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}\n{result.stderr}"
        )


def make_reference_document(path: Path = REFERENCE) -> Path:
    """Pandoc's default reference document, with ruled tables."""
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc is required to build the DOCX sources")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        default = Path(tmp) / "reference.docx"
        data = subprocess.run(
            [pandoc, "--print-default-data-file", "reference.docx"],
            capture_output=True,
            check=True,
        )
        default.write_bytes(data.stdout)
        with zipfile.ZipFile(default) as source:
            parts = {name: source.read(name) for name in source.namelist()}
        styles = parts["word/styles.xml"].decode("utf-8")
        if "<w:tblBorders>" in styles:
            patched = styles
        else:
            # Insert the rules into the definition of the Table style itself,
            # so every table Pandoc emits inherits them.
            patched = re.sub(
                r'(<w:style [^>]*w:styleId="Table".*?<w:tblPr>)',
                r"\1" + _TBL_BORDERS,
                styles,
                count=1,
                flags=re.DOTALL,
            )
            patched = re.sub(
                r'(<w:style [^>]*w:styleId="Table".*?)(</w:style>)',
                r"\1" + _TBL_RUN + r"\2",
                patched,
                count=1,
                flags=re.DOTALL,
            )
        if "<w:tblBorders>" not in patched:
            raise SystemExit("could not add table borders to the reference document")
        parts["word/styles.xml"] = patched.encode("utf-8")

        # A serif body and serif headings: the theme fonts are what Word uses
        # for everything the styles do not name explicitly.
        if "word/theme/theme1.xml" in parts:
            theme = parts["word/theme/theme1.xml"].decode("utf-8")
            theme = re.sub(
                r'<a:latin typeface="[^"]*"',
                '<a:latin typeface="Times New Roman"',
                theme,
            )
            parts["word/theme/theme1.xml"] = theme.encode("utf-8")

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
            for name, blob in parts.items():
                target.writestr(name, blob)
    return path


#: A4 with 25 mm margins: the publisher is in the United Kingdom, and Pandoc
#: writes no page size at all, which leaves Word's locale default (Letter).
_PAGE = (
    '<w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" '
    'w:header="709" w:footer="709" w:gutter="0"/>'
)


def to_docx(markdown: Path, docx: Path, reference: Path = REFERENCE) -> Path:
    run(
        [
            "pandoc",
            str(markdown),
            "-o",
            str(docx),
            f"--reference-doc={reference}",
            "--from=markdown+pipe_tables",
            # Pandoc resolves image paths against the working directory, not
            # the input file, so the figures have to be named explicitly.
            f"--resource-path={markdown.parent}",
        ]
    )
    set_page_size(docx)
    return docx


def set_page_size(docx: Path) -> None:
    """Give the document an explicit A4 page and 25 mm margins."""
    with zipfile.ZipFile(docx) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    body = parts["word/document.xml"].decode("utf-8")
    if "<w:pgSz" in body:
        return
    if "<w:sectPr" in body:
        # Pandoc writes an empty section properties block; give it a page.
        body = body.replace("<w:sectPr>", "<w:sectPr>" + _PAGE, 1)
    else:
        body = body.replace("</w:body>", f"<w:sectPr>{_PAGE}</w:sectPr></w:body>")
    parts["word/document.xml"] = body.encode("utf-8")
    with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as target:
        for name, blob in parts.items():
            target.writestr(name, blob)


def to_pdf(docx: Path, pdf: Path) -> Path:
    """Export the DOCX to PDF with Word, on a private application instance."""
    script = (
        "$ErrorActionPreference='Stop';"
        "$w = New-Object -ComObject Word.Application;"
        "$w.Visible = $false;"
        "$w.DisplayAlerts = 0;"
        f"$d = $w.Documents.Open('{docx}', $false, $true);"
        f"$d.ExportAsFixedFormat('{pdf}', 17);"
        "$d.Close($false);"
        "$w.Quit();"
    )
    run(["powershell", "-NoProfile", "-Command", script])
    if not pdf.exists():
        raise SystemExit(f"Word did not write {pdf}")
    return pdf


def page_count(pdf: Path) -> int:
    import pymupdf

    with pymupdf.open(pdf) as document:
        return document.page_count


def set_pdf_author(pdf: Path, author: str) -> None:
    """Put the author's name in the PDF metadata of the title page.

    Word's own PDF export writes no ``/Author``, and the anonymised
    manuscript must carry none, so the property is set here on the one
    document that names its author. The value is
    :data:`research.cpiv.measurement.build_manuscript.AUTHOR`, the same
    string the title page prints.
    """
    import pymupdf

    stamped = pdf.with_suffix(".stamped.pdf")
    with pymupdf.open(pdf) as document:
        metadata = dict(document.metadata)
        metadata["author"] = author
        document.set_metadata(metadata)
        document.save(stamped)
    stamped.replace(pdf)


def table_count(docx: Path) -> int:
    with zipfile.ZipFile(docx) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    return xml.count("<w:tbl>")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def public_files(files: list[Path]) -> list[Path]:
    """Drop the files that carry the author's name and contact details."""
    return [path for path in files if path.stem not in PRIVATE_STEMS]


def make_combined_markdown() -> Path:
    """Create a combined markdown file with title page, manuscript, and supplement."""
    combined = SUBMISSION / "combined.md"
    title_page_text = (SUBMISSION / "title_page.md").read_text(encoding="utf-8")
    manuscript_text = (MANUSCRIPT_DIR / "manuscript_jcf_draft.md").read_text(encoding="utf-8")
    # The *rendered* supplement, not the template: the template still carries
    # the `{{supplementary.strata_table}}` slot, so reading it shipped an
    # unfilled Table S1 into the combined document.
    supplement_text = (
        MANUSCRIPT_DIR / "manuscript_jcf_supplement.md"
    ).read_text(encoding="utf-8")
    # Concatenate: title page first, then manuscript, then supplement.
    # A raw OpenXML page break separates them. A bare "DIVIDER" line was used
    # before to keep pandoc from reading a leading "---" as YAML front matter,
    # but pandoc renders the word itself as visible body text; the page break
    # splits the sections without printing anything.
    page_break = (
        "\n```{=openxml}\n"
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n'
        "```\n"
    )
    combined.write_text(
        title_page_text
        + page_break
        + manuscript_text
        + page_break
        + supplement_text,
        encoding="utf-8",
    )
    return combined


def main() -> int:
    reference = make_reference_document()
    print(f"reference document: {reference.relative_to(ROOT)}")

    for name, markdown in DOCUMENTS:
        docx = SUBMISSION / f"{name}.docx"
        pdf = SUBMISSION / f"{name}.pdf"
        to_docx(markdown, docx, reference)
        to_pdf(docx, pdf)
        if name == "title_page":
            set_pdf_author(pdf, AUTHOR)
        print(
            f"{name}: docx {docx.stat().st_size // 1024} KiB, "
            f"pdf {page_count(pdf)} pages, {table_count(docx)} tables"
        )

    # Create combined markdown and PDF
    combined_md = make_combined_markdown()
    combined_docx = SUBMISSION / "combined.docx"
    combined_pdf = SUBMISSION / "combined.pdf"
    to_docx(combined_md, combined_docx, reference)
    to_pdf(combined_docx, combined_pdf)
    print(
        f"combined: docx {combined_docx.stat().st_size // 1024} KiB, "
        f"pdf {page_count(combined_pdf)} pages"
    )

    # Figures are also submitted as separate editable files, named by figure
    # number, and the manifest has to cover them.
    figure_dir = SUBMISSION / "figures"
    figure_dir.mkdir(exist_ok=True)
    for source in sorted((MANUSCRIPT_DIR / "figures").glob("figure_*.*")):
        shutil.copy2(source, figure_dir / source.name)

    # A package-wide check that the renderer left nothing behind. This runs
    # before the manifest is written so a failure cannot leave a manifest
    # hashing a known-bad file. `combined.md` and the supplement are included
    # deliberately: an earlier version checked only the draft and title page,
    # and the combined document shipped with an unfilled Table S1 slot as a
    # result, because `make_combined_markdown` used to read the supplement
    # *template* rather than the rendered supplement.
    _SLOT = re.compile(r"\{\{[^}]+\}\}")
    _LEAKED = re.compile(r"^DIVIDER$", re.MULTILINE)
    for markdown in (
        MANUSCRIPT_DIR / "manuscript_jcf_draft.md",
        MANUSCRIPT_DIR / "manuscript_jcf_supplement.md",
        SUBMISSION / "title_page.md",
        SUBMISSION / "combined.md",
    ):
        text = markdown.read_text(encoding="utf-8")
        if match := _SLOT.search(text):
            line = text[: match.start()].count("\n") + 1
            raise SystemExit(f"{markdown}:{line} still contains an unfilled slot")
        if match := _LEAKED.search(text):
            line = text[: match.start()].count("\n") + 1
            raise SystemExit(
                f"{markdown}:{line} contains a leaked DIVIDER marker; "
                "the combined build should emit a page break, not this text"
            )

    files = public_files(sorted(SUBMISSION.glob("*.docx")) + sorted(SUBMISSION.glob("*.pdf")))
    files += sorted((SUBMISSION / "tables").glob("*.csv"))
    files += sorted(figure_dir.glob("figure_*.*"))
    lines = [f"{sha256(path)}  {path.relative_to(SUBMISSION).as_posix()}" for path in files]
    manifest = SUBMISSION / "manifest.sha256"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"manifest: {manifest.relative_to(ROOT)} ({len(lines)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())