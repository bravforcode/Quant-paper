# CPIV R10 revision and release audit — final8, 10 October 2026

## Status and scope

This is a local proposed revision, not a submission, editorial decision, or
venue approval. The manuscript remains a synthetic numerical methods note. It
uses no historical option-chain data, market-wide position census, return
sample, or empirical alpha test. No external email, form, Google Doc, public
archive, or submission was sent or changed in this revision.

Review input: the user-supplied R10 review pasted on 10 October 2026. It reports
that the reviewer recalculated the 720-case grid and found the headline values
consistent. The attached source code, test suite, prior checksum manifest, and
CSV/JSON mentioned in that review were not all independently available as a
complete pre-existing package; this audit separately validates only the files
and checks listed below.

## Review corrections implemented

- Reworded the endpoint-symmetry explanation: absolute call-endpoint error at
  spread `+d` maps to absolute put-endpoint error at spread `-d`. Equal
  distributions do not imply equal call and put errors within each same cell.
- Added an approximate normal-theory Monte Carlo standard error for each
  simulated SD in Table 3, `s/sqrt(2(n-1))`, with `n=6,000`. The largest
  absolute difference between the gradient and simulation SD is about 1.37
  reported MCSEs; the manuscript does not interpret that difference as proof
  of nonlinearity.
- Reported normalized midpoint vega descriptively for the 96 cells that fail
  the absolute-vega guard. The median is `1.4039e-14`; nearest-rank p95 and
  maximum are `1.7239e-10` (rank 92); the range is `2.0644e-58` to
  `1.7239e-10`. No normalized cutoff is presented as validated or adopted.
- Replaced “wide tails” with “concave-magnitude” for the deterministic
  transformation `g(x)=sign(x)*sqrt(|x|)`. Its support remains `[-1,1]`; it is
  not described as a heavy-tailed distribution.
- Added the actual reproduction commands in Appendix B and split long
  PowerShell lines so the PDF does not clip them.
- Moved the interactive R8 widget to Appendix A under “R8 baseline
  illustration (not an R10 result)”; it is explicitly not an R10 result.

The review’s optional additions—an analytic Gaussian-inversion baseline,
chance turnover baseline, a summary table for every non-Gaussian noise family,
and an unequal-vega uncertainty case—were not added. They require new analyses
rather than correction of the identified presentation issues and remain
outside this revision.

## Numerical results and CSV provenance

The regenerated synthetic grid contains 720 cells: 624 pass the manuscript’s
configured absolute-vega guard and 96 fail it. For the 624 resolved cells,
midpoint absolute error has median `0.00007858 pp`, nearest-rank p95
`0.08720301 pp` (rank 593), and maximum `1.23551964 pp`. Each endpoint summary
is reported separately: median `0.02024694 pp`, p95 `1.17522948 pp`, maximum
`32.55474925 pp`. Their equal sorted summaries arise from the reflected
construction described above; they are not pooled into 1,248 observations and
are not market-weighted.

The user-supplied file
`C:/Users/menum/Downloads/r10_independent_approximation_grid_audit.csv` has
SHA-256
`3959A1E9FEBC888C589226ED86498BD0E02EF00D9E822384B9EB1D722D01C060`. The
review author says this CSV was generated in an earlier chat from the paper’s
specification using composite Simpson integration with 2,000 subintervals.
That is a reported attribution, not independently verified provenance: the
generating script and run record were not supplied for inspection. The review
also reports all 720 rows agree with its recomputation. This consistency
supports that the written specification can reproduce the grid; it is not an
independent human replication. The CSV is not included in the companion ZIP
because its script provenance and reuse rights are not established.

The canonical regenerated grid at
`research/cpiv/generated/revision_20261010_r10_proposed_final6/local_approximation_grid.csv`
has SHA-256
`4B778F039D7367F238FD5D711A19926C08BE46B1C25380E09111D0243C835B5D`, matching
the previously checked internal grid. This identity establishes artifact
continuity, not independent validation of the underlying model.

## Build and verification

- Rebuilt HTML, DOCX, and PDF from the updated R10 source and the regenerated
  synthetic assets.
- Focused test suite: **30 passed** across R10 diagnostics, artifact builder,
  and educational-demo tests.
- Ruff: **All checks passed** for the changed diagnostics, build script, and
  tests.
- `officecli validate` passed for the final8 DOCX. Structural inspection found
  four bordered native tables; Table 3 has seven rows and seven columns.
- PDF visual review: 14 A4 pages. Checked the Table 3/figure page, the Section
  8/table placement, disclosure and Appendix A page, and Appendix B commands;
  no clipped command text or orphan Section 8 heading remained.
- HTML inspection confirmed the widget is located under its R8-only label and
  the generated figures use the final6 asset set. The widget is illustrative,
  not a simulated R10 result.
- XeLaTeX/MiKTeX emitted a non-fatal update-check notice; the build completed
  with exit code 0.
- The companion package contains 195 files, including its manifest. All 194
  manifest entries match the staged files; the ZIP contains all 195 files,
  passes CRC validation, and its members match the staged bytes. The supplied
  CSV is absent. A scan for literal JWT-shaped strings found no matches; this
  limited scan is not a general secret audit.

These checks do not validate source permissions, venue fit, a public license,
or any empirical market claim. The article contains no market-data or alpha
evidence; the earlier liquidation-position G5 is not addressed or closed by
this CPIV revision.

## Final local artifacts

Under `dist/cpiv/r10-proposed-2026-10-10-final8/`:

| Format | File | Bytes | SHA-256 |
|---|---|---:|---|
| HTML | `quantcorner-cpiv-review-r10-2026-10-10.html` | 517,993 | `4FE6BC5CAB0600DD178E043DA9FEB5DD6462C9CDB1104AA58B5B8CA93E4D9FA1` |
| DOCX | `quantcorner-cpiv-review-r10-2026-10-10.docx` | 295,587 | `B0C9F1984FD1784B4E4F3F9CEA05FF24A41F77872EF035DB2DB8511E24A2A6C9` |
| PDF | `quantcorner-cpiv-review-r10-2026-10-10.pdf` | 392,464 | `8467B90A5118E3ABCCE302ECA14847DFFAEA7E20839334398AAC0F5A569C2E7D` |

The companion ZIP is a separate local reproducibility handoff. Its manifest
identifies bundled files only; hashes do not grant publication or redistribution
rights. The author must still verify sources, rights, and venue requirements
before external release.
