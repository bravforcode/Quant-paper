# Submission package — Journal of Computational Finance

Everything the publisher asks for at submission, built from the run artefacts in
`research/cpiv/measurement/outputs/`. The manuscript is anonymised; the title
page is a separate document; the appendices and two tables are separate
supplementary material; each table is also supplied as its own editable file.

## Files

| File | Purpose |
|:--|:--|
| [manuscript_jcf_draft.pdf](manuscript_jcf_draft.pdf) | The anonymised manuscript, 21 A4 pages, the file to upload |
| [manuscript_jcf_draft.docx](manuscript_jcf_draft.docx) | The Word source of that PDF (the "source file" the journal asks for on acceptance) |
| [title_page.pdf](title_page.pdf) / [title_page.docx](title_page.docx) | The separate title page |
| [manuscript_jcf_supplement.pdf](manuscript_jcf_supplement.pdf) / [.docx](manuscript_jcf_supplement.docx) | Supplementary material: Table S1 (strata), Table S2 (declared settings), Appendices A and B |
| [tables/](tables) | One CSV per main-text table, for the typesetter |
| [figures/](figures) | Figure 1 as a 300 dpi PNG and a vector PDF, copied in at build time from [../manuscript/figures/](../manuscript/figures) |
| [manifest.sha256](manifest.sha256) | SHA-256 of every file in this package |
| [reference.docx](reference.docx) | The Pandoc reference document used to build the DOCX files (ruled table style) |

The markdown sources live one level up in
[../manuscript/](../manuscript): `manuscript_jcf_draft.template.md`,
`manuscript_jcf_supplement.template.md`, and the rendered
`manuscript_jcf_draft.md` / `manuscript_jcf_supplement.md`.

## Compilation order

The journal states the order in which a submission must be compiled: title page
(separate), figure and table legends, abstract, keywords, key messages, title,
main text (blind), declarations of interest and acknowledgements, references.
`manuscript_jcf_draft.pdf` follows that order exactly; the title page is the
separate document the guidelines require, so the main file opens with the
legends rather than with the title. The paper has nothing to acknowledge, and
the guidelines only place actual acknowledgements under that heading, so the
`Acknowledgements` heading is omitted rather than left as an empty slot.

## What was verified

Every number in the manuscript is a `{{slot}}` filled from the run artefacts by
[build_manuscript.py](../../../research/cpiv/measurement/build_manuscript.py); a
slot with no value fails the build, and the build then refuses to write the
package if the result breaks a stated limit.

| Check | Result |
|:--|:--|
| Main text length (numbered Section 1 through Section 8, tables included) | 9 973 words — within the 10 000-word guidance; the same figure appears on the title page |
| Abstract | 198 words, one paragraph — within 150–200 |
| Keywords | 6 — within 4–6 |
| Key messages | 4, longest 71 characters — within 3–4 and 85 characters |
| Tables | 7 in the main text, each with a one-sentence legend and a prose citation; 2 in the supplement |
| Table geometry | every table's rows match its header width (a mismatch silently drops the last column) |
| Figures | one, with a one-sentence legend and a prose citation; in this package as a 300 dpi PNG and a vector PDF, both hashed in the manifest |
| References | 21, all cited in the text, all with DOIs where one exists, Chicago author-date in text with an APA list |
| Anonymity | the author's name does not appear in the manuscript |
| Rebuilt artifacts | `pytest tests -q` (full suite, run in the worktree on 2026-10-31): 269 passed; `ruff check research/cpiv/measurement scripts`: clean after the line-length fixes in `exploratory_seeds.py` |

The checks are enforced by
[manuscript_limits.py](../../../research/cpiv/measurement/manuscript_limits.py)
and covered by `tests/test_cpiv_measurement_manuscript.py`, so a later edit
cannot quietly break the format.

## What only the author can do

1. **Title page contact fields are filled** — affiliation [affiliation removed]; postal
   address [postal address removed]; email and corresponding-author email [email removed].
   They live in
   [build_manuscript.py](../../../research/cpiv/measurement/build_manuscript.py),
   so a rebuild keeps them; re-check them before submitting.
2. **Acknowledgements: none, decided.** There is no funding, collaborator or
   helper to acknowledge, so the heading was removed rather than left as an
   empty slot. If the author later wants to thank someone, restore the
   `## Acknowledgements` heading in the template above the declarations and
   rebuild.
3. **AI-use statement: edited 2026-10-29, extended to code assistance on the author's instruction.** It names each tool and its use: Perplexity for deep research, and Claude (Anthropic) as an editing aid for language and a coding aid for the analysis code. This matches the JCF Use of Artificial Intelligence section.
4. **Submit.** Nothing in this directory has been uploaded. The paper uses no market data, so no licence is needed. The vendor letters of 2026-10-29 are not part of this submission; their records are kept in [../licence_correspondence/](../licence_correspondence/).

## Rebuilding

```bash
.venv/Scripts/python.exe -m research.cpiv.measurement.build_manuscript
.venv/Scripts/python.exe scripts/build_jcf_submission.py
```

The first command renders the markdown, the title page and the table CSVs and
enforces the limits; the second builds the DOCX files with Pandoc, exports the
PDFs with Word, and rewrites `manifest.sha256`.
