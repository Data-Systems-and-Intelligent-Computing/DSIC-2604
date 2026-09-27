#!/usr/bin/env python
"""Run semantic equivalence check (Q1, Q2, Q3) across all layout variants.

Verifies that all 4 Iceberg table variants (ais_pos_08, ais_pos_16, ais_pos_32,
ais_pos_64) produce identical query results for Q1 (predicate scan count),
Q2 (selective aggregate), and Q3 (selective group-by).

This is Gate G5 prerequisite: semantic correctness must hold before the
benchmark results can be interpreted.

Outputs:
  - data/manifests/gate_equivalence_report.json

Prerequisites:
  - Lakehouse running (docker compose up -d)
  - All 4 variant tables populated by scripts/generate_all_variants.py
  - Gate G2/G3/G4 passed (audit_layouts.py)

Usage:
    python scripts/run_equivalence_check.py
    python scripts/run_equivalence_check.py --start 2023-08-01 --end 2023-08-08
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generate_layouts import ACTIVE_GRID, table_name
from src.validate_equivalence import run_equivalence_queries
from src.mmdec import AIS_POS_ROWS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_equivalence_check")

REPORT_PATH = PROJECT_ROOT / "data" / "manifests" / "gate_equivalence_report.json"

# Default predicate window: ~1 week mid-August 2023.
# AIS dataset covers 2023-07-07 to 2023-10-07 (93 days).
# This window has ~1.4M rows ~ 7.4% selectivity on Date column.
DEFAULT_START = "2023-08-15 00:00:00"
DEFAULT_END   = "2023-08-21 23:59:59"


def main():
    parser = argparse.ArgumentParser(
        description="Run Q1/Q2/Q3 equivalence check across all layout variants."
    )
    parser.add_argument(
        "--start", default=DEFAULT_START,
        help=f"Start timestamp for predicate window (default: {DEFAULT_START})"
    )
    parser.add_argument(
        "--end", default=DEFAULT_END,
        help=f"End timestamp for predicate window (default: {DEFAULT_END})"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("DSIC-2604 H6: Semantic Equivalence Check (Q1/Q2/Q3)")
    logger.info("=" * 60)
    logger.info(f"Predicate window: {args.start!r} -> {args.end!r}")
    logger.info(f"Variants: {[f'{m:02d}mib' for m in ACTIVE_GRID]}")

    tables = {f"{m:02d}mib": table_name(m) for m in ACTIVE_GRID}
    logger.info(f"Tables: {tables}")
    logger.info("")

    overall_passed = False
    results = {}
    error_msg = None

    try:
        results = run_equivalence_queries(
            table_names=tables,
            start_ts=args.start,
            end_ts=args.end,
            expected_total_rows=AIS_POS_ROWS,
        )
        overall_passed = all(v["status"] == "PASSED" for v in results.values())
    except AssertionError as e:
        error_msg = str(e)
        logger.error(f"Equivalence check FAILED: {e}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Unexpected error: {e}")
        raise

    # Log results
    logger.info("")
    logger.info("=" * 60)
    for qname, qresult in results.items():
        status = qresult.get("status", "ERROR")
        icon = "PASSED" if status == "PASSED" else "FAILED"
        logger.info(f"  {qname}: {icon}")

    if error_msg:
        logger.info(f"  Error: {error_msg}")

    logger.info("")
    if overall_passed:
        logger.info("OVERALL: ALL EQUIVALENCE CHECKS PASSED")
    else:
        logger.info("OVERALL: EQUIVALENCE CHECK FAILED")
    logger.info("=" * 60)

    # Save report
    report = {
        "check_date": datetime.now(timezone.utc).isoformat(),
        "predicate_window": {"start_ts": args.start, "end_ts": args.end},
        "variants_checked": list(tables.keys()),
        "expected_total_rows": AIS_POS_ROWS,
        "results": results,
        "overall": "PASSED" if overall_passed else "FAILED",
        "error": error_msg,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info(f"Report saved to {REPORT_PATH}")

    if not overall_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
