"""Browser, layout, and export checks for the built CPIV review artifacts.

Browser tests skip when Playwright's Chromium is missing or the built HTML is absent. Run
``uv run playwright install chromium`` once and build the release before running them. Set
``CPIV_ARTIFACT_DIR`` and ``CPIV_REVISION`` to check another build, and ``CPIV_SCREENSHOT_DIR``
to keep full-page screenshots for visual review.
"""

from __future__ import annotations

import os
import re
import zipfile
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "research/cpiv/manuscript_r11_proposed.md"
REVISION = os.environ.get("CPIV_REVISION", "r26")
ARTIFACT_DIR = Path(
    os.environ.get("CPIV_ARTIFACT_DIR", ROOT / "dist/cpiv/quantcorner-cpiv-reviewed-2026-10-18-v28")
).resolve()
STEM = f"quantcorner-cpiv-review-{REVISION}-2026-10-18"
HTML = ARTIFACT_DIR / f"{STEM}.html"
DOCX = ARTIFACT_DIR / f"{STEM}.docx"
PDF = ARTIFACT_DIR / f"{STEM}.pdf"
SCREENSHOT_DIR = os.environ.get("CPIV_SCREENSHOT_DIR")

# MathML elements in the built HTML. Update when an equation is added or removed.
EXPECTED_MATH_ELEMENTS = 317  # 305 inline + 12 display in the r26 manuscript (r25: 282)
EXPECTED_FIGURES = 5
MINIMUM_TABLES = 10
PHONE_WIDTH = 375
DESKTOP_WIDTH = 1280
GUTTER_PX = 16

HEADING_LINE = re.compile(r"^(\d+(\.\d+)?\.?\s+\S.{0,70}|Appendix [A-C]\..{0,70}|References)$")


class _Session:
    """One Chromium page that blocks network requests and records console errors."""

    def __init__(self, browser: Any, width: int) -> None:
        self.context = browser.new_context(viewport={"width": width, "height": 900})
        self.page = self.context.new_page()
        self.errors: list[str] = []
        self.blocked: list[str] = []
        self.page.on(
            "console",
            lambda message: self.errors.append(message.text) if message.type == "error" else None,
        )
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.route("http://**", self._block)
        self.page.route("https://**", self._block)

    def _block(self, route: Any) -> None:
        self.blocked.append(route.request.url)
        route.abort()

    def open(self) -> Any:
        self.page.goto(HTML.as_uri(), wait_until="load")
        self.page.wait_for_function(
            "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
            timeout=15_000,
        )
        return self.page

    def close(self) -> None:
        self.context.close()


@pytest.fixture(scope="module")
def browser() -> Any:
    from playwright.sync_api import sync_playwright

    if not HTML.is_file():
        pytest.skip(f"built HTML not found: {HTML}")
    with sync_playwright() as playwright:
        if not Path(playwright.chromium.executable_path).is_file():
            pytest.skip("Playwright Chromium is not installed; run playwright install chromium")
        chromium = playwright.chromium.launch(
            headless=True, args=["--disable-background-networking"]
        )
        try:
            yield chromium
        finally:
            chromium.close()


def _session(browser: Any, width: int) -> _Session:
    return _Session(browser, width)


def _appendix_b_commands() -> list[str]:
    appendix = MANUSCRIPT.read_text(encoding="utf-8").split(
        "## Appendix B. Reproduction commands", maxsplit=1
    )[1]
    block = re.search(r"```text\r?\n(.*?)```", appendix, re.S)
    assert block is not None, "Appendix B has no text code block"
    return [line.strip() for line in block.group(1).splitlines() if line.strip()]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def test_html_structure_math_figures_and_alt_text(browser: Any) -> None:
    session = _session(browser, DESKTOP_WIDTH)
    try:
        page = session.open()
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
                tables: document.querySelectorAll('table').length,
                figures: document.querySelectorAll('figure').length,
                images: Array.from(document.images).map(img => img.alt.trim()),
              };
            }"""
        )
        assert stats["math"] == EXPECTED_MATH_ELEMENTS
        assert stats["rendered"] == stats["math"]
        assert stats["tables"] >= MINIMUM_TABLES
        assert stats["figures"] == EXPECTED_FIGURES
        assert len(stats["images"]) == EXPECTED_FIGURES
        assert all(alt for alt in stats["images"]), "every figure needs non-empty alt text"
        assert session.blocked == []
        assert session.errors == []
    finally:
        session.close()


@pytest.mark.parametrize("width", [PHONE_WIDTH, DESKTOP_WIDTH])
def test_no_horizontal_page_scroll(browser: Any, width: int) -> None:
    session = _session(browser, width)
    try:
        page = session.open()
        widths = page.evaluate(
            "() => ({scroll: document.documentElement.scrollWidth,"
            " client: document.documentElement.clientWidth})"
        )
        assert widths["scroll"] <= widths["client"] + 1, widths
        if SCREENSHOT_DIR:
            Path(SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(SCREENSHOT_DIR) / f"html-{width}px.png"), full_page=True)
    finally:
        session.close()


def test_phone_content_keeps_sixteen_pixel_gutter(browser: Any) -> None:
    session = _session(browser, PHONE_WIDTH)
    try:
        page = session.open()
        offenders = page.evaluate(
            """(gutter) => {
              const scrollBox = el => {
                for (let p = el.parentElement; p; p = p.parentElement) {
                  const o = getComputedStyle(p).overflowX;
                  if (o === 'auto' || o === 'scroll' || o === 'hidden') return true;
                }
                return false;
              };
              const width = document.documentElement.clientWidth;
              const selector = 'main p, main h1, main h2, main h3, main h4, main li, '
                + 'main figure, main table, main math';
              return Array.from(document.querySelectorAll(selector))
                .filter(el => !scrollBox(el))
                .map(el => ({el, r: el.getBoundingClientRect()}))
                .filter(({r}) => r.width > 0 && (r.left < gutter - 0.5
                  || width - r.right < gutter - 0.5))
                .map(({el, r}) => ({tag: el.tagName, text: el.textContent.trim().slice(0, 60),
                  left: r.left, right: width - r.right}));
            }""",
            GUTTER_PX,
        )
        assert offenders == [], offenders[:5]
    finally:
        session.close()


def test_noise_widget_slider_updates_output(browser: Any) -> None:
    session = _session(browser, DESKTOP_WIDTH)
    try:
        page = session.open()
        slider = page.locator("#cpiv-noise-range")
        assert slider.get_attribute("max") == "6"
        before = page.locator("#cpiv-noise-output").inner_text()
        slider.evaluate(
            "node => { node.value = node.max; node.dispatchEvent(new Event('input')); }"
        )
        after = page.locator("#cpiv-noise-output").inner_text()
        assert before != after
        assert page.locator("#cpiv-noise-ranking li").count() > 0
        assert session.errors == []
    finally:
        session.close()


def test_appendix_b_commands_match_source_in_html(browser: Any) -> None:
    session = _session(browser, DESKTOP_WIDTH)
    try:
        page = session.open()
        code_text = page.evaluate(
            "() => Array.from(document.querySelectorAll('pre')).map(p => p.innerText).join('\\n')"
        )
    finally:
        session.close()
    for command in _appendix_b_commands():
        assert command in code_text, command


def test_docx_figures_have_descriptions() -> None:
    if not DOCX.is_file():
        pytest.skip(f"built DOCX not found: {DOCX}")
    with zipfile.ZipFile(DOCX) as package:
        document = package.read("word/document.xml").decode("utf-8")
    descriptions = re.findall(r'<wp:docPr\b[^>]*\bdescr="([^"]*)"', document)
    assert len(descriptions) == EXPECTED_FIGURES
    assert all(text.strip() for text in descriptions)


def test_docx_contains_appendix_b_commands() -> None:
    if not DOCX.is_file():
        pytest.skip(f"built DOCX not found: {DOCX}")
    with zipfile.ZipFile(DOCX) as package:
        document = package.read("word/document.xml").decode("utf-8")
    paragraphs = [
        "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", paragraph))
        for paragraph in re.findall(r"<w:p\b.*?</w:p>", document, re.S)
    ]
    text = _normalise("\n".join(paragraphs))
    for command in _appendix_b_commands():
        assert _normalise(command) in text, command


def test_pdf_has_no_blank_pages_or_stranded_headings() -> None:
    fitz = pytest.importorskip("pymupdf")
    if not PDF.is_file():
        pytest.skip(f"built PDF not found: {PDF}")
    document = fitz.open(PDF)
    try:
        blank: list[int] = []
        stranded: list[tuple[int, str]] = []
        for number, page in enumerate(document, start=1):
            text = page.get_text()
            if not text.strip() and not page.get_images() and not page.get_drawings():
                blank.append(number)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if lines and HEADING_LINE.match(lines[-1]):
                stranded.append((number, lines[-1]))
        assert blank == []
        assert stranded == []
    finally:
        document.close()


def test_pdf_contains_appendix_b_commands() -> None:
    fitz = pytest.importorskip("pymupdf")
    if not PDF.is_file():
        pytest.skip(f"built PDF not found: {PDF}")
    document = fitz.open(PDF)
    try:
        text = _normalise(" ".join(page.get_text() for page in document))
    finally:
        document.close()
    for command in _appendix_b_commands():
        assert _normalise(command) in text, command
