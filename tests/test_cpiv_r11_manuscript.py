from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "research/cpiv/manuscript_r11_proposed.md"


def test_manuscript_has_no_internal_revision_or_machine_path_leaks() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    body, appendix = manuscript.split("## Appendix B. Reproduction commands", maxsplit=1)
    for internal in (
        "R8",
        "R10",
        "R11",
        "legacy guard",
        "legacy cutoff",
        "r10_",
        "r11_",
        "cpivR11OutputDir",
        r"C:\paper\quant-paper",
    ):
        assert internal.casefold() not in manuscript.casefold()

    assert 'date: "18 October 2026"' in manuscript
    assert "15.92548%" in manuscript and "17.07114%" in manuscript
    assert "11.4326 basis points" in manuscript and "0.114326%" in manuscript
    assert "one-basis-point forward mismatch corresponds locally to 0.087469 CPIV points" in body
    assert "the synthetic pair has" in body and r"\(R=0\), so \(X_C=X_P" in body
    assert r"\min(X_C,X_P)" in body
    assert "base premium" not in manuscript.split("### 6.5", maxsplit=1)[1].split(
        "## 7. Results", maxsplit=1
    )[0]
    assert "X_C-X_P" in body and "only when" in body
    assert "median per-configuration log-log slope is 3.0003" in body
    assert "0.04238 pp" in body and "1.4767 pp" in body
    assert (
        "research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-12_v2/"
        "local_approximation_error.png"
    ) in body
    captions = re.findall(r"\*\*Table (\d+)([A-Z]?)\.\*\*", manuscript)
    assert captions == [(str(number), "") for number in range(1, 11)]
    prose = "\n".join(
        line
        for line in manuscript.splitlines()
        if not line.startswith("**Table ")
        and not line.startswith("|")
        and not line.startswith("![")
    )
    for number in range(1, 11):
        assert f"Table {number}" in prose
    for number in range(1, 6):
        assert f"Figure {number}" in prose
    section8 = manuscript.split("## 8. Interpretation and limits", maxsplit=1)[1].split(
        "## 9. Reproducibility and declarations", maxsplit=1
    )[0]
    assert "**Table 10.**" in section8
    disclosure = manuscript.split(
        "## 9. Reproducibility and declarations", maxsplit=1
    )[1].split("**Funding and in-kind support:**", maxsplit=1)[0]
    assert "624/96" in disclosure
    assert "0.00007858/0.087203/1.23552 pp" in disclosure
    assert "median 3.0003" in disclosure and "2.8733–3.0441" in disclosure
    assert "every signed reference-offset summary in Table 1" in disclosure
    assert "same written grid specification" in disclosure
    assert "specification errors may be shared" in disclosure
    assert "The common-map identity checker covers" in body
    assert "zero-bid" in body.casefold() or "bid = 0" in body
    assert "unresolved partial order" in body
    assert "no DOI has been assigned" in body
    assert "no public repository, reuse license, or DOI-backed archive" in appendix
    assert "has not been executed" in appendix
    assert "No external cash funding was received" in manuscript
    assert "complimentary one-month HyperTracker Surge subscription" in manuscript
    assert "The provider supplied no data or analytical input for this note" in manuscript
    assert "no HyperTracker data are used" in manuscript
    assert "broader project" not in manuscript.casefold()
    assert "The author declares no competing interests" in manuscript


def test_manuscript_defines_identification_separately_from_iv_tolerance() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    methods = manuscript.split("### 6.5", maxsplit=1)[1].split("## 7. Results", maxsplit=1)[0]
    results = manuscript.split("### 7.7", maxsplit=1)[1].split("### 7.8", maxsplit=1)[0]
    table6 = manuscript.split("**Table 6.**", maxsplit=1)[1].split(
        "**Table 7.**", maxsplit=1
    )[0]
    table7 = manuscript.split("**Table 7.**", maxsplit=1)[1].split(
        "![Finite-shock identification", maxsplit=1
    )[0]
    protocol = manuscript.split("**Table 10.**", maxsplit=1)[1].split(
        "## 9. Reproducibility and declarations", maxsplit=1
    )[0]

    assert "identified" in methods.casefold()
    assert "within" in methods.casefold() and "tau_{IV}" in methods
    assert "worst-direction displacement from the base IV" in methods
    assert "0.087469" in results and "0.043735" in results and "0.05" in results
    assert r"\pm t/2" in results
    assert "unresolved" in results.casefold()
    assert "tau_{IV}=0.10" in table6 and "tau_{IV}=0.05" in table6
    assert "price-unit shock (pp)" in table6
    assert "+0.0875" in table6 and "Yes | Yes | No" in table6
    assert "Partial: 7.0717" in table6 and "OTM-equivalent value below tick" in table6
    assert "No root" in table6 and "Unresolved" in table6
    assert r"\pm t/2=\pm0.005" in table7
    assert "Yes / Yes" in table7 and "5.9264" in table7
    assert "predeclared \\(\\tau_{IV}\\)" in protocol
    assert "identified within" in protocol.casefold()
    assert "identified outside" in protocol.casefold()
    assert r"\min(X_C,X_P)" in protocol
    assert "worst-direction displacement" in protocol
    assert "unresolved / local-only" in protocol


def test_zero_bid_is_retained_as_one_sided_unresolved_rank_information() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    rank_stage = manuscript.split("| Rank diagnostics |", maxsplit=1)[1].split("\n", maxsplit=1)[0]
    section = manuscript.split("### 6.3", maxsplit=1)[1].split("### 6.4", maxsplit=1)[0]

    assert "retain one-sided bounds" in rank_stage
    assert "including incomplete endpoint cases" in rank_stage
    assert "discard the pair" in section.casefold()
    assert "unresolved partial-order comparisons" in section.casefold()


def test_appendix_reproduction_claims_are_limited_to_observed_environment() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    appendix = manuscript.split("## Appendix B. Reproduction commands", maxsplit=1)[1]

    assert "uv` 0.11.8" in appendix
    assert "Python 3.12 or newer" in appendix
    assert "Python 3.14.3" in appendix
    assert "Python 3.13 each completed the reproduction" in appendix
    assert "105 passed and 10 skipped" in appendix
    assert "at most 3.34e-10" in appendix
    assert "byte identity across platforms is not claimed" in appendix
    assert "matrix for Python 3.12–3.14" in appendix
    assert "has not been executed" in appendix
    assert "intended for both PowerShell and Bash" in appendix
    assert "executed verbatim in PowerShell on Windows" in appendix
    assert "establishes determinism, not independent correctness" in appendix
    assert "no public repository, reuse license, or DOI-backed archive" in appendix
    assert (
        appendix.count(
            "python -m scripts.reproduce_cpiv_methods --output research/cpiv/generated/repro"
        )
        == 1
    )
    assert appendix.count("python -m pytest tests -q") == 1
    assert "R8" not in appendix and "R10" not in appendix and "R11" not in appendix
    assert "284 tests" not in appendix and "286 tests" not in appendix
