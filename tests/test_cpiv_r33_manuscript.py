from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "research/cpiv/manuscript_r33_proposed.md"


def _manuscript() -> str:
    return MANUSCRIPT.read_text(encoding="utf-8")


def test_r33_figure_paths_exist() -> None:
    paths = re.findall(r"\]\((research/cpiv/generated/[^)\s]+\.png)\)", _manuscript())
    assert len(paths) == 5
    for relative in paths:
        assert (ROOT / relative).is_file(), relative


def test_r33_section_8_points_to_licence_limit() -> None:
    assert "A real option-chain illustration is therefore not included (Section 9)" in _manuscript()


def test_r33_section_9_states_licence_limit() -> None:
    manuscript = _manuscript()
    assert "Bybit Card Terms and Conditions, section 15" in manuscript
    assert "No public chain with a clear publication licence was found" in manuscript


def test_r33_appendix_d_records_revision() -> None:
    assert "- **r33 (20 October 2026).**" in _manuscript()
