#!/usr/bin/env python
"""Generate all 4 Parquet layout variants for DSIC-2604 H6.

Reads the canonical MMDEC dataset (Dataset_AIS_POS.parquet) and writes
4 Iceberg tables with target file sizes [8, 16, 32, 64] MiB.

All other writer properties are held constant:
  - row-group target: 8 MiB
  - compression: snappy
  - partitioning: unpartitioned
  - row order: Date-clustered (ORDER BY Date)
  - schema & values: identical

Prerequisites:
  - Lakehouse must be running (docker compose up -d)
  - PySpark + Iceberg packages available
  - Java 17+ installed

Usage:
    python scripts/generate_all_variants.py [--drop]
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generate_layouts import (
    ACTIVE_GRID,
    COMPRESSION,
    ROW_GROUP_TARGET_MIB,
    build_all_variants,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("generate_all_variants")

# Canonical dataset path
CANONICAL_DATASET = PROJECT_ROOT / "Dataset" / "Dataset_AIS_POS.parquet"
WRITE_COST_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "write_cost_manifest.csv"
GENERATION_LOG = PROJECT_ROOT / "data" / "manifests" / "generation_log.json"


def write_cost_csv(results, output_path):
    """Write write_cost_manifest.csv from generation results."""
    header = (
        "variant,target_file_size_mib,layout_build_wall_seconds,"
        "write_throughput_mib_s,generated_file_count,storage_footprint_mib,"
        "rewrite_compaction_seconds,writer_version,spark_version,"
        "iceberg_version,recorded_at"
    )

    # We'll fill what we can; file counts will be populated by audit_layouts.py
    lines = [header]
    now = datetime.now(timezone.utc).isoformat()

    for r in results:
        # Rough throughput: canonical size / wall time
        canonical_mib = 450.05
        throughput = canonical_mib / r["wall_seconds"] if r["wall_seconds"] > 0 else 0

        line = ",".join([
            r["variant"],
            str(r["target_file_size_mib"]),
            f"{r['wall_seconds']:.2f}",
            f"{throughput:.2f}",
            "",  # generated_file_count (filled by audit)
            "",  # storage_footprint_mib (filled by audit)
            "",  # rewrite_compaction_seconds (N/A for initial write)
            "pyspark-3.5.6",
            "3.5.6",
            "1.9.1",
            now,
        ])
        lines.append(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info(f"Write cost manifest saved to {output_path}")


def save_generation_log(results, output_path):
    """Save detailed generation log as JSON."""
    log = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canonical_dataset": str(CANONICAL_DATASET),
        "grid": ACTIVE_GRID,
        "row_group_target_mib": ROW_GROUP_TARGET_MIB,
        "compression": COMPRESSION,
        "variants": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Generation log saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate all Parquet layout variants.")
    parser.add_argument(
        "--drop", action="store_true",
        help="Drop and recreate existing tables before writing."
    )
    parser.add_argument(
        "--source", type=str, default=str(CANONICAL_DATASET),
        help=f"Path to canonical Parquet file (default: {CANONICAL_DATASET})"
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        logger.error(f"Canonical dataset not found: {source}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("DSIC-2604 H6: Generate Layout Variants")
    logger.info("=" * 60)
    logger.info(f"Source: {source}")
    logger.info(f"Grid: {ACTIVE_GRID} MiB")
    logger.info(f"Row-group target: {ROW_GROUP_TARGET_MIB} MiB")
    logger.info(f"Compression: {COMPRESSION}")
    logger.info(f"Drop existing: {args.drop}")
    logger.info("")

    results = build_all_variants(source, drop_existing=args.drop)

    # Save write cost manifest
    write_cost_csv(results, WRITE_COST_MANIFEST)

    # Save generation log
    save_generation_log(results, GENERATION_LOG)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 60)
    total_time = sum(r["wall_seconds"] for r in results)
    for r in results:
        logger.info(f"  {r['variant']:>6s}: {r['row_count']:>12,} rows, "
                     f"{r['wall_seconds']:>7.1f}s -> {r['table_name']}")
    logger.info(f"  Total wall time: {total_time:.1f}s")
    logger.info("")
    logger.info("Next step: run scripts/audit_layouts.py to verify Gate G2/G3/G4")


if __name__ == "__main__":
    main()
