.PHONY: test smoke layouts calibrate benchmark analyze

test:
	pytest -q
smoke:
	bash scripts/run_smoke.sh
layouts:
	bash scripts/build_layouts.sh
calibrate:
	bash scripts/calibrate_selectivity.sh
benchmark:
	bash scripts/run_main_benchmark.sh
analyze:
	bash scripts/analyze_results.sh
