"""Entry point untuk main benchmark / dry-run.

Pengganti run_main_benchmark.sh untuk dijalankan di Windows PowerShell.

Usage:
    python scripts/run_benchmark.py           # full run (1.584 total)
    python scripts/run_benchmark.py --dry-run  # 72 query, 1 blok, no warmup
"""
import sys
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.benchmark import run_benchmark

dry_run = "--dry-run" in sys.argv

report = run_benchmark(dry_run=dry_run)

# Simpan summary report
report_path = Path("data/manifests/benchmark_summary_report.json")
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print()
print("=" * 60)
print("Benchmark complete." + (" [DRY-RUN]" if dry_run else ""))
print(f"  Total runs    : {report['total_runs']}")
print(f"  Measured runs : {report['measured_runs']}")
print(f"  Failed        : {report['failed']}")
print(f"  Missing telem : {report['missing_telemetry_runs']}")
print(f"  Wall time     : {report['wall_time_seconds']:.1f}s")
print(f"  Raw log       : {report['raw_log_path']}")
print(f"  Report        : {report_path}")
print("=" * 60)

if report["failed"] > 0:
    sys.exit(1)
