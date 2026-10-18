"""Remove source-path alt text that Pandoc copies into DOCX picture properties.

Pandoc writes each image's alt text into wp:docPr and repeats the image's
source path in pic:cNvPr. The alt text stays on wp:docPr, so only the
path-valued attribute is removed. Run after build_cpiv_review.py.
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
import zipfile
from pathlib import Path

PATH_DESCR = re.compile(rb'\sdescr="research/cpiv/[^"]*"')


def strip_path_descriptions(docx_path: Path, expected_count: int) -> int:
    with zipfile.ZipFile(docx_path) as source:
        entries = [(item, source.read(item.filename)) for item in source.infolist()]
    document_xml = next(
        payload for item, payload in entries if item.filename == "word/document.xml"
    )
    updated_xml, removed = PATH_DESCR.subn(b"", document_xml)
    if removed != expected_count:
        raise ValueError(
            f"expected {expected_count} path-valued alt attributes, found {removed}"
        )

    with tempfile.NamedTemporaryFile(
        prefix=f"{docx_path.stem}-alt-", suffix=".tmp", dir=docx_path.parent,
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
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("expected_count", type=int)
    args = parser.parse_args()
    removed = strip_path_descriptions(args.docx, args.expected_count)
    print(f"removed {removed} path-valued alt attributes")


if __name__ == "__main__":
    main()
