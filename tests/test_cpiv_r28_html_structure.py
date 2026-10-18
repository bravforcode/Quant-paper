"""Structure checks for the built r28 review HTML: MathML count, figures, alt text, no errors.

Kept separate from tests/test_cpiv_html_browser.py, whose expected counts are for r26 and are
covered by the v25-v28 manifests. Browser checks skip when Playwright's Chromium is missing or
the built HTML is absent.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = Path(
    os.environ.get("CPIV_ARTIFACT_DIR", ROOT / "dist/cpiv/quantcorner-cpiv-reviewed-2026-10-18-r28")
).resolve()
HTML = ARTIFACT_DIR / "quantcorner-cpiv-review-r28-2026-10-18.html"
# 317 MathML elements in the r26 and r27 manuscripts; r28 adds 15 inline equations (per-name stress text).
EXPECTED_MATH_ELEMENTS = 332
EXPECTED_FIGURES = 5


def test_r28_html_math_figures_and_alt_text() -> None:
    if not HTML.is_file():
        pytest.skip(f"built HTML not found: {HTML}")
    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    blocked: list[str] = []

    def block(route: object) -> None:
        blocked.append(route.request.url)  # type: ignore[attr-defined]
        route.abort()  # type: ignore[attr-defined]

    with sync_playwright() as playwright:
        if not Path(playwright.chromium.executable_path).is_file():
            pytest.skip("Playwright Chromium is not installed; run playwright install chromium")
        browser = playwright.chromium.launch(headless=True, args=["--disable-background-networking"])
        try:
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.route("http://**", block)
            page.route("https://**", block)
            page.goto(HTML.as_uri(), wait_until="load")
            page.wait_for_function(
                "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
                timeout=15_000,
            )
            stats = page.evaluate(
                """() => {
                  const math = Array.from(document.querySelectorAll('math'));
                  const rendered = math.filter(m => {
                    const r = m.getBoundingClientRect();
                    return r.width > 0 && r.height > 0;
                  });
                  return {
                    math: math.length,
                    rendered: rendered.length,
                    figures: document.querySelectorAll('figure').length,
                    images: Array.from(document.images).map(img => img.alt.trim()),
                  };
                }"""
            )
            context.close()
        finally:
            browser.close()

    assert stats["math"] == EXPECTED_MATH_ELEMENTS
    assert stats["rendered"] == stats["math"]
    assert stats["figures"] == EXPECTED_FIGURES
    assert len(stats["images"]) == EXPECTED_FIGURES
    assert all(alt for alt in stats["images"]), "every figure needs non-empty alt text"
    assert blocked == []
    assert errors == []
