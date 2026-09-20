#!/usr/bin/env bash
# ==============================================================================
# DSIC-2604: Main Factorial Benchmark (Minggu 2, H9-H11)
#
# Menjalankan block-randomized factorial benchmark:
#   4 file sizes × 6 selectivity bands × 3 query families = 72 conditions
#   × (2 warm-up + 20 measured) = 1,584 total runs
#
# Prerequisites:
#   - Docker stack running (MinIO + Iceberg REST + Trino)
#   - All 4 variant tables registered in Iceberg catalog
#   - Pilot benchmark passed (G5, G6, G8, G9)
#
# Usage:
#   bash scripts/run_main_benchmark.sh
#   bash scripts/run_main_benchmark.sh --dry-run  # observability check only
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

echo "================================================================="
echo "DSIC-2604 — Main Factorial Benchmark"
echo "================================================================="
echo "Start time: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# Run the benchmark
python -u -c "
import logging
import json
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)

from src.benchmark import run_benchmark

dry_run = '--dry-run' in sys.argv

report = run_benchmark(dry_run=dry_run)

# Save summary report
report_path = Path('data/manifests/benchmark_summary_report.json')
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

print()
print('=' * 60)
print(f'Benchmark complete.')
print(f'  Total runs:    {report[\"total_runs\"]}')
print(f'  Measured runs: {report[\"measured_runs\"]}')
print(f'  Failed:        {report[\"failed\"]}')
print(f'  Missing telem: {report[\"missing_telemetry_runs\"]}')
print(f'  Wall time:     {report[\"wall_time_seconds\"]:.1f}s')
print(f'  Raw log:       {report[\"raw_log_path\"]}')
print(f'  Report:        {report_path}')
print('=' * 60)

if report['failed'] > 0:
    sys.exit(1)
" "$@"

echo "End time: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
