"""Submission limits and format rules for the JCF manuscript.

The rules are the ones the publisher states in its submission guidelines
(Risk Journals, "Submission Guidelines", as published for *The Journal of
Computational Finance*):

* a research paper should not exceed 10 000 words;
* the abstract is one paragraph of 150 to 200 words;
* 4 to 6 keywords follow the abstract;
* 3 to 4 key messages, each no more than 85 characters;
* the compiled manuscript is anonymous, and the title page is separate;
* every reference in the list is cited in the text, in Chicago author-date
  style with an APA-formatted list.

The module measures a rendered manuscript and reports every violation it
finds. It reads the rendered text, not the template, so a slot that renders
to the wrong thing is caught the same way a hand-typed number is.

Usage::

    .venv/Scripts/python.exe -m research.cpiv.measurement.manuscript_limits \
        docs/cpiv-jcf/manuscript/manuscript_jcf_draft.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

#: Words in the main text, per the publisher's guidance (not a strict policy,
#: but the manuscript should not need the exception).
MAX_MAIN_TEXT_WORDS = 10_000
ABSTRACT_MIN_WORDS = 150
ABSTRACT_MAX_WORDS = 200
MIN_KEYWORDS = 4
MAX_KEYWORDS = 6
MIN_KEY_MESSAGES = 3
MAX_KEY_MESSAGES = 4
MAX_KEY_MESSAGE_CHARS = 85
MAX_SHORT_TITLE_CHARS = 50

#: The author's name must not appear in the anonymised manuscript.
AUTHOR_NAME = "Phirawit Jitnarong"

_EMPHASIS = re.compile(r"[*_`]+")
_SEPARATOR = re.compile(r"^\|(:?-{2,}:?\|)+$")
_TABLE_ROW = re.compile(r"^\s*\|")
_SLOT = re.compile(r"\{\{[^}]+\}\}")


def words(text: str) -> int:
    """Whitespace-separated tokens, with markdown emphasis markers removed."""
    return len(_EMPHASIS.sub("", text).split())


def _section(text: str, heading: str) -> str:
    """The body of the ``## heading`` section, up to the next ``## ``."""
    lines = text.split("\n")
    start = None
    for index, line in enumerate(lines):
        if start is None:
            if line.strip().lower() == heading.lower():
                start = index + 1
        elif line.startswith("## "):
            return "\n".join(lines[start:index])
    if start is None:
        return ""
    return "\n".join(lines[start:])


def _main_text(text: str) -> str:
    """The numbered sections, from 1 up to the declarations."""
    lines = text.split("\n")
    start = end = None
    for index, line in enumerate(lines):
        if start is None and re.match(r"^##\s+1\.\s", line):
            start = index
        elif start is not None and re.match(r"^##\s+Declarations of Interest", line):
            end = index
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end])


def _table_captions(text: str) -> list[str]:
    """Numbers of the table captions in the body, in order of appearance."""
    return re.findall(r"^\*\*Table (\d+)\.\s", text, flags=re.MULTILINE)


def _figure_captions(text: str) -> list[str]:
    """Numbers of the figures, read from the caption of each embedded image."""
    return re.findall(r"^!\[\*\*Figure (\d+)\.", text, flags=re.MULTILINE)


def _legend_numbers(text: str, prefix: str = "Table") -> list[str]:
    """Numbers of the entries in the separate figure and table legends."""
    legends = _section(text, "## Figure and table legends")
    return re.findall(
        rf"^\*\*{prefix} (\d+)\.\*\*", legends, flags=re.MULTILINE
    )


def _prose(text: str) -> str:
    """The main text without table rows, so a caption cannot cite itself."""
    keep: list[str] = []
    for line in text.split("\n"):
        if _TABLE_ROW.match(line) or line.lstrip().startswith("**Table "):
            continue
        keep.append(line)
    return "\n".join(keep)


def _cells(line: str) -> int:
    return len(line.strip().strip("|").split("|"))


def _table_shape_problems(text: str) -> list[str]:
    """Tables whose rows disagree with the separator that defines the columns."""
    problems: list[str] = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if not _SEPARATOR.match(line):
            continue
        width = _cells(line)
        for neighbour in (index - 1, *range(index + 1, len(lines))):
            if not lines[neighbour].lstrip().startswith("|"):
                break
            if _cells(lines[neighbour]) != width:
                problems.append(
                    f"a table row on line {neighbour + 1} has "
                    f"{_cells(lines[neighbour])} cells against a {width}-column header"
                )
            if neighbour > index and not lines[neighbour].lstrip().startswith("|"):
                break
    return problems


def _reference_surnames(text: str) -> list[str]:
    """First-author surnames from the APA reference list."""
    block = _section(text, "## References")
    surnames: list[str] = []
    for line in block.split("\n"):
        match = re.match(r"^([A-Z][A-Za-z'\-\u00C0-\u024F]+),", line.strip())
        if match:
            surnames.append(match.group(1))
    return surnames


@dataclass
class Report:
    """The measured facts about a rendered manuscript, and the violations."""

    abstract_words: int
    abstract_paragraphs: int
    keywords: int
    key_messages: int
    longest_key_message: int
    main_text_words: int
    tables: int
    figures: int
    references: int
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def summary(self) -> str:
        rows = [
            ("abstract words", f"{self.abstract_words}", "150-200"),
            ("abstract paragraphs", f"{self.abstract_paragraphs}", "1"),
            ("keywords", f"{self.keywords}", "4-6"),
            ("key messages", f"{self.key_messages}", "3-4"),
            ("longest key message", f"{self.longest_key_message}", "<= 85 chars"),
            ("main text words", f"{self.main_text_words}", "<= 10000"),
            ("numbered tables", f"{self.tables}", "-"),
            ("numbered figures", f"{self.figures}", "-"),
            ("references", f"{self.references}", "-"),
        ]
        width = max(len(name) for name, _, _ in rows)
        lines = [f"{name:<{width}}  {value:>8}   {limit}" for name, value, limit in rows]
        if self.warnings:
            lines.append("")
            lines += [f"warning: {warning}" for warning in self.warnings]
        if self.violations:
            lines.append("")
            lines += [f"FAIL: {violation}" for violation in self.violations]
        else:
            lines.append("")
            lines.append("all submission limits met")
        return "\n".join(lines)


def check(text: str) -> Report:
    """Measure ``text`` and return a :class:`Report` listing any violations."""
    abstract = _section(text, "## Abstract").strip()
    paragraphs = [block for block in re.split(r"\n\s*\n", abstract) if block.strip()]
    keyword_block = _section(text, "## Keywords")
    keywords = [item.strip() for item in keyword_block.split(";") if item.strip()]
    message_block = _section(text, "## Key messages")
    messages = [
        re.sub(_EMPHASIS, "", line.strip()[2:].strip())
        for line in message_block.split("\n")
        if line.strip().startswith("- ")
    ]
    main = _main_text(text)
    captions = _table_captions(text)
    surnames = _reference_surnames(text)

    report = Report(
        abstract_words=words(abstract),
        abstract_paragraphs=len(paragraphs),
        keywords=len(keywords),
        key_messages=len(messages),
        longest_key_message=max((len(message) for message in messages), default=0),
        main_text_words=words(main),
        tables=len(captions),
        figures=len(_figure_captions(text)),
        references=len(surnames),
    )

    def fail(message: str) -> None:
        report.violations.append(message)

    if not ABSTRACT_MIN_WORDS <= report.abstract_words <= ABSTRACT_MAX_WORDS:
        fail(
            f"abstract is {report.abstract_words} words; the limit is "
            f"{ABSTRACT_MIN_WORDS}-{ABSTRACT_MAX_WORDS}"
        )
    if report.abstract_paragraphs != 1:
        fail(f"abstract has {report.abstract_paragraphs} paragraphs; it must be one")
    if not MIN_KEYWORDS <= report.keywords <= MAX_KEYWORDS:
        fail(f"{report.keywords} keywords; the limit is {MIN_KEYWORDS}-{MAX_KEYWORDS}")
    if not MIN_KEY_MESSAGES <= report.key_messages <= MAX_KEY_MESSAGES:
        fail(
            f"{report.key_messages} key messages; the limit is "
            f"{MIN_KEY_MESSAGES}-{MAX_KEY_MESSAGES}"
        )
    if report.longest_key_message > MAX_KEY_MESSAGE_CHARS:
        fail(
            f"a key message is {report.longest_key_message} characters; the limit "
            f"is {MAX_KEY_MESSAGE_CHARS}"
        )
    if report.main_text_words > MAX_MAIN_TEXT_WORDS:
        fail(
            f"main text is {report.main_text_words} words; the guidance is "
            f"{MAX_MAIN_TEXT_WORDS}"
        )

    # The compiled document carries the legends, so every table needs one and
    # every table must be pointed at from the prose.
    legends = _legend_numbers(text)
    prose = _prose(main)
    for number in captions:
        if number not in legends:
            fail(f"Table {number} has no entry in the figure and table legends")
        if not re.search(rf"\bTable {number}\b", prose):
            fail(f"Table {number} is never cited in the main text")
    for number in legends:
        if number not in captions:
            fail(f"the legends list Table {number}, which is not in the main text")

    # The same rule for figures: each needs a legend, a caption, and a mention
    # in the prose that is not the caption itself.
    figures = _figure_captions(text)
    for number in figures:
        if number not in _legend_numbers(text, prefix="Figure"):
            fail(f"Figure {number} has no entry in the figure and table legends")
        if not re.search(rf"\bFigure {number}\b", prose):
            fail(f"Figure {number} is never cited in the main text")

    # Chicago author-date style cites by surname and year, so a reference
    # whose surname never appears in the text is uncited.
    for surname in surnames:
        if surname not in main:
            fail(f"reference {surname} is not cited in the main text")

    # A pipe table whose separator row has a different width from its header
    # loses its last column in every renderer, silently.
    for problem in _table_shape_problems(text):
        fail(problem)

    if AUTHOR_NAME in text:
        fail("the anonymised manuscript contains the author's name")

    if _SLOT.search(text):
        fail("the manuscript still contains an unfilled template slot")

    if not text.lstrip().startswith("<!--"):
        report.warnings.append(
            "the document does not open with the compilation-order comment"
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript", type=Path)
    args = parser.parse_args(argv)
    text = args.manuscript.read_text(encoding="utf-8")
    report = check(text)
    print(report.summary())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
