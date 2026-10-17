# Call–Put Implied-Volatility Spreads (CPIV)

Review package and reproduction code for a measurement note on call–put
implied-volatility spreads (CPIV). The note maps paired European
Black–Scholes–Merton (BSM) inversions exactly and tests how reliable the spread
is under synthetic quote noise.

## Definition

For a matched call–put pair (same underlying, strike, expiry, exercise style,
and multiplier):

```
CPIV = 100 × (σ_C − σ_P)
```

The value is in percentage points, where σ_C and σ_P are the call and put
implied volatilities.

## Scope

- Every reported result is synthetic: European BSM inputs and simulated quote
  noise. The note uses no market quotes, option chains, returns, positions, or
  liquidation data.
- The note makes no alpha or trading claim.
- The repository also contains Hyperliquid collection and analysis code from a
  separate liquidation-exposure project. That code is outside the CPIV package
  and is not described here.

## Contents

| Path | Purpose |
|---|---|
| `research/cpiv/manuscript_r11_proposed.md` | Working manuscript (dated 18 October 2026) |
| `research/cpiv/*.py` | Diagnostics, audits, and benchmarks |
| `research/cpiv/generated/` | Generated CSV, JSON, SVG, and PNG evidence |
| `dist/cpiv/quantcorner-cpiv-reviewed-2026-10-18-v28/` | v28 (r26) review package: HTML, DOCX, PDF |
| `reports/cpiv_v28_manifest_2026-10-18.sha256` | SHA-256 manifest for the v28 package (268 entries) |
| `reports/cpiv_v28_manifest_cpiv-only_2026-10-18.sha256` | SHA-256 manifest for the CPIV-only subset (171 entries) |
| `tests/test_cpiv_*.py` | CPIV tests |

## Reproduce

Requires Python 3.12 or later and [uv](https://docs.astral.sh/uv/). CI runs the
test suite on Ubuntu and Windows with Python 3.12, 3.13, and 3.14.

```bash
uv sync --locked --no-install-project
uv run python -m pytest tests -q
```

Regenerate the synthetic methods-note outputs into a fresh folder. The script
refuses to write into a non-empty folder:

```bash
uv run python scripts/reproduce_cpiv_methods.py --output research/cpiv/generated/<fresh-name>
```

Verify the v28 package against its manifest:

```bash
pwsh -File scripts/verify_sha256_manifest.ps1 -ManifestPath reports/cpiv_v28_manifest_2026-10-18.sha256 -RootPath .
```

The manifests do not cover `README.md` or `CITATION.cff`.

## Limitations

- This is a measurement and methods note. It reports no empirical CPIV result.
- Simulated rankings and quote-noise results describe only the chosen synthetic
  generator and seeds.
- No independent replication by an outside party has been done.

## Citing the CPIV review package (v28)

The CPIV review package (v28, r26, dated 18 October 2026) is archived on Zenodo:

- Version DOI: https://doi.org/10.5281/zenodo.23442601
- All versions (concept DOI): https://doi.org/10.5281/zenodo.23442600

Citation metadata is in `CITATION.cff`; the code is licensed under MIT (`LICENSE`).
