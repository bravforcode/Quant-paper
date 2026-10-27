"""The public manifest leaves out the title page and the combined check copy."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "docs" / "cpiv-jcf" / "submission"


def _build_script():
    spec = importlib.util.spec_from_file_location(
        "build_jcf_submission", ROOT / "scripts" / "build_jcf_submission.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_files_drop_the_title_page_and_combined_copy() -> None:
    build = _build_script()
    files = [
        SUBMISSION / name
        for name in (
            "manuscript_jcf_draft.docx",
            "manuscript_jcf_draft.pdf",
            "title_page.docx",
            "title_page.pdf",
            "combined.docx",
            "combined.pdf",
        )
    ]

    kept = [path.name for path in build.public_files(files)]

    assert kept == ["manuscript_jcf_draft.docx", "manuscript_jcf_draft.pdf"]


def test_the_committed_manifest_names_no_private_file() -> None:
    manifest = (SUBMISSION / "manifest.sha256").read_text(encoding="utf-8")

    assert "title_page." not in manifest
    assert "combined." not in manifest
