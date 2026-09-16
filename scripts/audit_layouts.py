#!/usr/bin/env python
"""Audit generated Parquet layout variants for DSIC-2604 H6.

Inspects all 4 Iceberg tables written by generate_all_variants.py and
verifies Gate G2 (completeness), G3 (IQR separation), and G4 (row-group control).

Outputs:
  - data/manifests/layout_manifest.csv
  - data/manifests/gate_g2g3g4_audit_report.json
  - Updates file counts in data/manifests/write_cost_manifest.csv

Prerequisites:
  - Lakehouse must be running
  - All 4 variant tables must exist in Iceberg catalog

Usage:
    python scripts/audit_layouts.py
"""
import json
import logging
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.client import Config as BotoConfig

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generate_layouts import ACTIVE_GRID, COMPRESSION, ROW_GROUP_TARGET_MIB, table_name
from src.inspect_parquet import (
    file_size_separation,
    grid_is_feasible,
    inspect_directory,
    row_group_control,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("audit_layouts")

LAYOUT_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "layout_manifest.csv"
WRITE_COST_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "write_cost_manifest.csv"
AUDIT_REPORT = PROJECT_ROOT / "data" / "manifests" / "gate_g2g3g4_audit_report.json"


def get_s3_client():
    """Create a boto3 S3 client targeting MinIO."""
    endpoint = os.getenv("MINIO_ENDPOINT_HOST", os.getenv("MINIO_ENDPOINT", "http://localhost:9000"))
    if "minio:" in endpoint and not os.path.exists("/.dockerenv"):
        endpoint = endpoint.replace("minio:", "localhost:")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.getenv("MINIO_ROOT_USER", "dsic2604"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "dsic2604desman"),
        region_name="us-east-1",
        config=BotoConfig(signature_version="s3v4"),
    )


def download_variant_files(s3, bucket, table_prefix, target_mib, tmp_dir):
    """Download all .parquet data files for a variant from MinIO.

    Iceberg stores data under:
      s3://dsic2604/warehouse/dsic2604/<table_name>/data/*.parquet
    """
    tbl_name = f"{table_prefix}_{target_mib:02d}"
    prefix = f"warehouse/dsic2604/{tbl_name}/data/"
    variant_dir = Path(tmp_dir) / f"{target_mib:02d}mib"
    variant_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading files from s3://{bucket}/{prefix} ...")

    paginator = s3.get_paginator("list_objects_v2")
    file_count = 0
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".parquet"):
                fname = key.split("/")[-1]
                local_path = variant_dir / fname
                with open(local_path, "wb") as f:
                    s3.download_fileobj(bucket, key, f)
                file_count += 1

    logger.info(f"  Downloaded {file_count} parquet files for {target_mib} MiB variant")
    return variant_dir, file_count


def write_layout_manifest(inspections, output_path):
    """Write layout_manifest.csv from inspection results."""
    header = (
        "variant,target_file_size_mib,actual_file_count,median_file_size_mib,"
        "iqr_file_size_mib,min_file_size_mib,max_file_size_mib,cv_file_size,"
        "row_group_target_mib,median_row_group_mib,row_count,checksum,"
        "compression,row_order,partitioning"
    )
    lines = [header]

    for target_mib, info in sorted(inspections.items()):
        line = ",".join([
            f"{target_mib:02d}mib",
            str(target_mib),
            str(info["file_count"]),
            f"{info['file_size_mib_median']:.2f}" if info["file_size_mib_median"] else "",
            f"{info['file_size_mib_iqr']:.2f}" if info.get("file_size_mib_iqr") else "",
            f"{info['file_size_mib_min']:.2f}" if info["file_size_mib_min"] else "",
            f"{info['file_size_mib_max']:.2f}" if info["file_size_mib_max"] else "",
            f"{info['file_size_cv']:.4f}" if info.get("file_size_cv") else "",
            str(ROW_GROUP_TARGET_MIB),
            f"{info['row_group_mib_median']:.2f}" if info["row_group_mib_median"] else "",
            str(info["row_count"]),
            "",  # checksum computed per-variant is complex; skip for now
            COMPRESSION,
            "date_clustered_fixed",
            "unpartitioned",
        ])
        lines.append(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info(f"Layout manifest saved to {output_path}")


def update_write_cost_manifest(inspections, manifest_path):
    """Update write_cost_manifest.csv with generated_file_count and storage_footprint_mib."""
    if not manifest_path.exists():
        logger.warning(f"Write cost manifest not found: {manifest_path}")
        return

    lines = manifest_path.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) < 2:
        return

    header = lines[0]
    updated = [header]

    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 11:
            updated.append(line)
            continue

        variant_label = parts[0]
        target_mib = int(parts[1]) if parts[1] else 0

        if target_mib in inspections:
            info = inspections[target_mib]
            parts[4] = str(info["file_count"])
            parts[5] = f"{info['total_size_mib']:.2f}"

        updated.append(",".join(parts))

    manifest_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    logger.info(f"Updated write cost manifest: {manifest_path}")


def main():
    logger.info("=" * 60)
    logger.info("DSIC-2604 H6: Audit Layout Variants")
    logger.info("=" * 60)

    s3 = get_s3_client()
    bucket = os.getenv("MINIO_BUCKET", "dsic2604")

    inspections = {}
    all_passed = True

    with tempfile.TemporaryDirectory(prefix="dsic2604_audit_") as tmp_dir:
        # Download and inspect each variant
        for target_mib in ACTIVE_GRID:
            try:
                variant_dir, file_count = download_variant_files(
                    s3, bucket, "ais_pos", target_mib, tmp_dir
                )
                if file_count == 0:
                    logger.error(f"  ❌ No files found for {target_mib} MiB variant!")
                    all_passed = False
                    continue

                info = inspect_directory(variant_dir)
                inspections[target_mib] = info

                logger.info(f"  {target_mib:>3d} MiB: {info['file_count']} files, "
                           f"median={info['file_size_mib_median']:.2f} MiB, "
                           f"rows={info['row_count']:,}, "
                           f"rg_median={info['row_group_mib_median']:.2f} MiB")
            except Exception as e:
                logger.error(f"  ❌ Error inspecting {target_mib} MiB variant: {e}")
                all_passed = False

    # ---- Gate G2: Layout Completeness ----
    g2_passed = len(inspections) == len(ACTIVE_GRID)
    logger.info("")
    logger.info(f"Gate G2 (Layout Completeness): "
                f"{'PASSED' if g2_passed else 'FAILED'} "
                f"({len(inspections)}/{len(ACTIVE_GRID)} variants)")

    # ---- Gate G3: IQR Separation ----
    g3_results = []
    g3_passed = True
    sorted_sizes = sorted(inspections.keys())

    for i in range(len(sorted_sizes) - 1):
        s_small = sorted_sizes[i]
        s_large = sorted_sizes[i + 1]
        if s_small in inspections and s_large in inspections:
            sep = file_size_separation(inspections[s_small], inspections[s_large])
            g3_results.append({
                "pair": f"{s_small}vs{s_large}",
                **sep,
            })
            if not sep["separated"]:
                g3_passed = False
                logger.warning(f"  ⚠️ {s_small} vs {s_large} MiB: NOT separated "
                              f"(ratio={sep['median_ratio']:.2f}, overlap={sep['iqr_overlap']})")
            else:
                logger.info(f"  ✓ {s_small} vs {s_large} MiB: separated "
                           f"(ratio={sep['median_ratio']:.2f})")

    logger.info(f"Gate G3 (IQR Separation): {'PASSED' if g3_passed else 'FAILED'}")

    # ---- Gate G3 addendum: feasibility of largest condition ----
    if sorted_sizes:
        largest = sorted_sizes[-1]
        feas = grid_is_feasible(inspections[largest])
        logger.info(f"Gate G3 (Feasibility): file_count={feas['file_count']}, "
                    f"feasible={feas['feasible']}, preferred={feas['preferred_met']}")
        if not feas["feasible"]:
            g3_passed = False

    # ---- Gate G4: Row-group Control ----
    variants_dict = {str(k): inspections[k] for k in inspections}
    g4_result = row_group_control(variants_dict)
    g4_passed = g4_result["controlled"]
    logger.info(f"Gate G4 (Row-group Control): "
                f"{'PASSED' if g4_passed else 'FAILED'} "
                f"(spread={g4_result['relative_spread']:.4f})")
    for k, v in g4_result["row_group_mib_median_by_variant"].items():
        logger.info(f"  {k} MiB: rg_median = {v:.2f} MiB")

    # ---- Summary ----
    overall = g2_passed and g3_passed and g4_passed
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"OVERALL: {'ALL GATES PASSED ✅' if overall else 'SOME GATES FAILED ❌'}")
    logger.info(f"  G2 (Completeness): {'PASSED' if g2_passed else 'FAILED'}")
    logger.info(f"  G3 (Separation):   {'PASSED' if g3_passed else 'FAILED'}")
    logger.info(f"  G4 (Row-group):    {'PASSED' if g4_passed else 'FAILED'}")
    logger.info("=" * 60)

    # ---- Write outputs ----
    if inspections:
        write_layout_manifest(inspections, LAYOUT_MANIFEST)
        update_write_cost_manifest(inspections, WRITE_COST_MANIFEST)

    # Audit report JSON
    report = {
        "audit_date": datetime.now(timezone.utc).isoformat(),
        "gates": {
            "G2": {"status": "PASSED" if g2_passed else "FAILED",
                   "variants_found": len(inspections),
                   "variants_expected": len(ACTIVE_GRID)},
            "G3": {"status": "PASSED" if g3_passed else "FAILED",
                   "separation_results": g3_results,
                   "feasibility": feas if sorted_sizes else None},
            "G4": {"status": "PASSED" if g4_passed else "FAILED",
                   "row_group_control": g4_result},
        },
        "variant_summaries": {
            f"{k:02d}mib": {
                "file_count": v["file_count"],
                "row_count": v["row_count"],
                "file_size_mib_median": v["file_size_mib_median"],
                "file_size_mib_iqr": v.get("file_size_mib_iqr"),
                "row_group_mib_median": v["row_group_mib_median"],
                "total_size_mib": v["total_size_mib"],
            }
            for k, v in sorted(inspections.items())
        },
        "overall": "PASSED" if overall else "FAILED",
    }

    AUDIT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Audit report saved to {AUDIT_REPORT}")

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()
