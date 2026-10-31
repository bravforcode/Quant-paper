.PHONY: setup test test-leakage typecheck import-check quality notebooks viz viz-part1 site serve export-standalone reproduce-synthetic

setup:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

reproduce-synthetic:
	python -m research.cpiv.measurement.synthetic

test-leakage:
	python -m pytest -q tests/leakage

typecheck:
	python -m mypy src/bti --ignore-missing-imports

import-check:
	python -m pip install --editable . --no-deps
	lint-imports --config importlinter.ini --no-cache

quality: typecheck import-check
	python -m ruff check src scripts tests

notebooks:
	python scripts/check_notebook.py notebooks/01_identifiability_demo.ipynb

viz: viz-part1

viz-part1:
	python scripts/build_part1.py

site:
	python scripts/export_combined_manuscript.py
	python -m mkdocs build -f site/mkdocs.yml

serve:
	python scripts/export_combined_manuscript.py
	python -m mkdocs serve -f site/mkdocs.yml

export-standalone:
	python scripts/export_part1.py

collect:
	@echo "UNVERIFIED: live collector is not enabled in this Part 1 checkout."

collect-daemon:
	@echo "UNVERIFIED: deploy only after API audit, ToS review, and G1."

health:
	@echo "UNVERIFIED: no live collector health snapshot exists."

backfill:
	@echo "UNVERIFIED: public backfill is not implemented for this scoped delivery."

coverage-report:
	@echo "UNVERIFIED: no raw position dataset exists."

freeze-config:
	python scripts/hash_configs.py

unlock-holdout:
	@echo "LOCKED: preregistration, clean git state, and manual authorization are required."
