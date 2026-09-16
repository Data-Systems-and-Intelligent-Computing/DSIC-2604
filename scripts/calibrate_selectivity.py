#!/usr/bin/env python
"""Calibrate selectivity bands for DSIC-2604 H7 (Gate G5/G6).

Executes COUNT(*) queries via Trino against the baseline variant (ais_pos_32)
to find Date window boundaries that achieve 6 target selectivity bands:
  S1=0.001, S2=0.01, S3=0.05, S4=0.20, S5=0.50, S6=0.90

Uses binary search on Date range duration, anchored at a fixed start
(2023-07-07 00:00:00 = first day of dataset) to ensure determinism.

Gate G5: All 6 bands within 20% relative error of their target.
Gate G6: Bands are monotonically ordered (measured selectivity strictly
         increases from S1 to S6).

Outputs:
  - data/manifests/selectivity_manifest.csv
  - data/manifests/gate_g5g6_selectivity_report.json

Prerequisites:
  - Lakehouse running
  - At least the baseline table (ais_pos_32) must be populated
  - Gate G2/G3/G4 passed

Usage:
    python scripts/calibrate_selectivity.py
    python scripts/calibrate_selectivity.py --table iceberg.dsic2604.ais_pos_32
    python scripts/calibrate_selectivity.py --dry-run
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.calibrate_selectivity import (
    SelectivityBand,
    audit_bands,
    initial_window_estimate,
    measured_selectivity,
)
from src.mmdec import AIS_POS_ROWS, OBSERVATION_START
from src.validate_equivalence import get_trino_connection, run_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("calibrate_selectivity")

SELECTIVITY_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "selectivity_manifest.csv"
SELECTIVITY_REPORT   = PROJECT_ROOT / "data" / "manifests" / "gate_g5g6_selectivity_report.json"

# 6 target selectivity bands (protocol_freeze.yaml § selectivity_bands)
TARGET_BANDS = [0.001, 0.01, 0.05, 0.20, 0.50, 0.90]

# Tolerance for G5 acceptance
BAND_TOLERANCE = 0.20  # ±20% relative error

# Anchor: dataset starts 2023-07-07
ANCHOR_START = datetime(2023, 7, 7, 0, 0, 0)

# Total rows (matches AIS_POS_ROWS)
TOTAL_ROWS = AIS_POS_ROWS

# Binary search parameters
MAX_ITER  = 20        # max bisection steps per band
MIN_DELTA = timedelta(minutes=1)


def count_rows(conn, table, start_ts, end_ts):
    """Run COUNT(*) with Date BETWEEN predicate on a Trino table."""
    start_str = start_ts.strftime("%Y-%m-%d %H:%M:%S")
    end_str   = end_ts.strftime("%Y-%m-%d %H:%M:%S")
    sql = (
        f"SELECT COUNT(*) AS n FROM {table} "
        f"WHERE \"Date\" BETWEEN TIMESTAMP '{start_str}' AND TIMESTAMP '{end_str}'"
    )
    result = run_query(conn, sql)
    return int(result[0]["n"])


def bisect_window(conn, table, target_sel, anchor, lo_delta, hi_delta, max_iter=MAX_ITER):
    """Binary search for a Date window achieving target selectivity.

    Args:
        conn: Trino connection
        table: Trino table name (fully qualified)
        target_sel: Target selectivity fraction (0, 1]
        anchor: Fixed start datetime
        lo_delta: Initial lower bound for window duration
        hi_delta: Initial upper bound for window duration
        max_iter: Maximum bisection iterations

    Returns:
        (end_ts, matched_rows, measured_sel)
    """
    target_rows = target_sel * TOTAL_ROWS
    best_end    = anchor + hi_delta
    best_rows   = count_rows(conn, table, anchor, best_end)
    best_sel    = best_rows / TOTAL_ROWS

    for i in range(max_iter):
        mid_delta = lo_delta + (hi_delta - lo_delta) / 2
        if mid_delta < MIN_DELTA:
            break
        mid_end  = anchor + mid_delta
        mid_rows = count_rows(conn, table, anchor, mid_end)
        mid_sel  = mid_rows / TOTAL_ROWS

        logger.debug(
            f"  iter {i+1}: window={mid_delta}, rows={mid_rows:,}, sel={mid_sel:.4%}"
        )

        if mid_rows <= target_rows:
            lo_delta  = mid_delta
        else:
            hi_delta  = mid_delta
            best_end  = mid_end
            best_rows = mid_rows
            best_sel  = mid_sel

        # Early exit if within tolerance
        rel_err = abs(mid_sel - target_sel) / target_sel
        if rel_err <= BAND_TOLERANCE:
            best_end  = mid_end
            best_rows = mid_rows
            best_sel  = mid_sel
            break

    return best_end, best_rows, best_sel


def calibrate_all_bands(conn, table, dry_run=False):
    """Calibrate all 6 selectivity bands via binary search.

    Returns list of SelectivityBand dataclasses.
    """
    bands = []

    # Estimate dataset date range (93 days from anchor)
    dataset_end = ANCHOR_START + timedelta(days=93)
    total_span  = dataset_end - ANCHOR_START

    for target in TARGET_BANDS:
        logger.info(f"--- Calibrating band target={target:.3f} ---")

        # Initial estimate from uniform distribution assumption
        est = initial_window_estimate(target)
        est_minutes = est["window_minutes"]
        logger.info(f"  Uniform estimate: {est_minutes:.1f} min ({est_minutes/60:.2f} h)")

        if dry_run:
            # Use estimate directly (no Trino queries)
            est_delta = timedelta(minutes=est_minutes)
            end_ts    = ANCHOR_START + est_delta
            est_rows  = int(target * TOTAL_ROWS)
            band = SelectivityBand(
                target=target,
                start_ts=ANCHOR_START.strftime("%Y-%m-%d %H:%M:%S"),
                end_ts=end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                matched_rows=est_rows,
                total_rows=TOTAL_ROWS,
            )
            logger.info(
                f"  [DRY RUN] end={band.end_ts}, rows~={est_rows:,}, sel~={target:.4%}"
            )
        else:
            # Binary search bounds: 0.5x – 2.0x of uniform estimate
            lo = timedelta(minutes=max(1, est_minutes * 0.5))
            hi = timedelta(minutes=min(est_minutes * 2.0, total_span.total_seconds() / 60))

            end_ts, matched, sel = bisect_window(
                conn, table, target, ANCHOR_START, lo, hi
            )
            rel_err = abs(sel - target) / target
            band = SelectivityBand(
                target=target,
                start_ts=ANCHOR_START.strftime("%Y-%m-%d %H:%M:%S"),
                end_ts=end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                matched_rows=matched,
                total_rows=TOTAL_ROWS,
            )
            icon = "OK" if band.accepted(BAND_TOLERANCE) else "WARN"
            logger.info(
                f"  [{icon}] end={band.end_ts}, rows={matched:,}, "
                f"measured={sel:.4%}, rel_err={rel_err:.1%}"
            )

        bands.append(band)

    return bands


def write_selectivity_manifest(bands, output_path):
    """Write selectivity_manifest.csv."""
    header = (
        "query_id,query_family,target_selectivity,measured_selectivity,"
        "predicate_start,predicate_end,matched_rows,total_rows,frozen_at"
    )
    now = datetime.now(timezone.utc).isoformat()
    lines = [header]
    for i, band in enumerate(bands, 1):
        qid = f"S{i}"
        family = "Q1_Q2_Q3"
        lines.append(",".join([
            qid,
            family,
            f"{band.target:.4f}",
            f"{band.measured:.6f}",
            band.start_ts,
            band.end_ts,
            str(band.matched_rows),
            str(band.total_rows),
            now,
        ]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info(f"Selectivity manifest saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate selectivity bands for H7 (Gate G5/G6)."
    )
    parser.add_argument(
        "--table", default="iceberg.dsic2604.ais_pos_32",
        help="Baseline Iceberg table to use for COUNT(*) calibration"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Skip Trino queries; use uniform distribution estimate only"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("DSIC-2604 H7: Selectivity Calibration (Gate G5/G6)")
    logger.info("=" * 60)
    logger.info(f"Baseline table : {args.table}")
    logger.info(f"Target bands   : {TARGET_BANDS}")
    logger.info(f"Anchor start   : {ANCHOR_START.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Dry run        : {args.dry_run}")
    logger.info("")

    conn = None if args.dry_run else get_trino_connection()

    try:
        bands = calibrate_all_bands(conn, args.table, dry_run=args.dry_run)
    finally:
        if conn:
            conn.close()

    # Gate G5: all bands within tolerance
    audit = audit_bands(bands, BAND_TOLERANCE)
    g5_passed = audit["all_accepted"]
    g6_passed = audit["monotonic"]

    logger.info("")
    logger.info("=" * 60)
    logger.info("CALIBRATION RESULTS")
    logger.info("=" * 60)
    for row in audit["bands"]:
        icon = "PASSED" if row["accepted"] else "FAILED"
        logger.info(
            f"  S{TARGET_BANDS.index(row['target'])+1} target={row['target']:.3f}: "
            f"measured={row['measured']:.4%}, rel_err={row['relative_error']:.1%} [{icon}]"
        )

    logger.info("")
    logger.info(f"Gate G5 (All bands within {BAND_TOLERANCE:.0%}): {'PASSED' if g5_passed else 'FAILED'}")
    logger.info(f"Gate G6 (Monotonically ordered):                 {'PASSED' if g6_passed else 'FAILED'}")
    logger.info("=" * 60)

    # Write manifest and report
    write_selectivity_manifest(bands, SELECTIVITY_MANIFEST)

    report = {
        "calibration_date": datetime.now(timezone.utc).isoformat(),
        "baseline_table": args.table,
        "dry_run": args.dry_run,
        "anchor_start": ANCHOR_START.strftime("%Y-%m-%d %H:%M:%S"),
        "total_rows": TOTAL_ROWS,
        "tolerance": BAND_TOLERANCE,
        "gates": {
            "G5": {"status": "PASSED" if g5_passed else "FAILED"},
            "G6": {"status": "PASSED" if g6_passed else "FAILED"},
        },
        "bands": [
            {
                "query_id": f"S{i}",
                "target": b.target,
                "measured": b.measured,
                "relative_error": b.relative_error,
                "accepted": b.accepted(BAND_TOLERANCE),
                "start_ts": b.start_ts,
                "end_ts": b.end_ts,
                "matched_rows": b.matched_rows,
            }
            for i, b in enumerate(bands, 1)
        ],
        "overall": "PASSED" if (g5_passed and g6_passed) else "FAILED",
    }

    SELECTIVITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SELECTIVITY_REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(f"Report saved: {SELECTIVITY_REPORT}")

    if not (g5_passed and g6_passed):
        sys.exit(1)


if __name__ == "__main__":
    main()
