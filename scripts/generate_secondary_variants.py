#!/usr/bin/env python3
"""
DSIC-2604: H23 — GENERATE SECONDARY PARQUET VARIANTS (Dataset_AIS_SPEC)
========================================================================
Tujuan:
  Menghasilkan 4 varian Parquet terkontrol dari Dataset_AIS_SPEC.parquet:
    - ais_spec_08 (target 8 MiB)
    - ais_spec_16 (target 16 MiB)
    - ais_spec_32 (target 32 MiB)
    - ais_spec_64 (target 64 MiB)
  
Kontrol Metodologis Tetap (Ceteris Paribus):
  - Row-group target: 8 MiB (8,388,608 bytes)
  - Kompresi: Snappy
  - Partisi: Unpartitioned
  - Row order: Date-clustered (ORDER BY Date)
  - Engine: PySpark + Iceberg REST Catalog

Deliverable:
  - Tabel Iceberg: iceberg.dsic2604.ais_spec_{08, 16, 32, 64}
  - data/manifests/secondary_write_cost_manifest.csv
"""

import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generate_layouts import (
    _get_s3_client,
    _purge_s3_table_data,
    _drop_iceberg_table_via_rest,
    get_spark_session,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("H23-SecondaryVariants")

SOURCE_PATH = PROJECT_ROOT / "Dataset" / "Dataset_AIS_SPEC.parquet"
OUTPUT_MANIFEST = PROJECT_ROOT / "data" / "manifests" / "secondary_write_cost_manifest.csv"

# Konfigurasi Grid Varian Sekunder (~210 MiB compressed)
SECONDARY_GRID = [8, 16, 32, 64]
ROW_GROUP_TARGET_BYTES = 8 * 1024 * 1024  # 8 MiB
COMPRESSION = "snappy"
TABLE_PREFIX = "ais_spec"
ICEBERG_SCHEMA = "dsic2604"
ICEBERG_CATALOG = "iceberg"

# Alokasi jumlah file target berdasarkan ukuran fisik ~210 MiB:
FILE_COUNTS = {
    64: 4,   # ~52.5 MiB / file
    32: 7,   # ~30.0 MiB / file
    16: 14,  # ~15.0 MiB / file
    8:  26,  # ~8.0 MiB / file
}

def build_secondary_variant(spark, target_mib: int):
    tbl_short = f"{TABLE_PREFIX}_{target_mib:02d}"
    full_table_name = f"{ICEBERG_CATALOG}.{ICEBERG_SCHEMA}.{tbl_short}"
    target_bytes = target_mib * 1024 * 1024
    num_files = FILE_COUNTS[target_mib]

    logger.info(f"=== Menulis Varian Sekunder: {tbl_short} (Target: {target_mib} MiB, {num_files} files) ===")

    # 1. Bersihkan catalog & S3 jika sebelumnya ada
    _drop_iceberg_table_via_rest(tbl_short)
    _purge_s3_table_data(tbl_short)

    # 2. Baca dataset sumber
    df = spark.read.parquet(str(SOURCE_PATH))

    # 3. Konversi kolom Date dari nanoseconds (bigint) ke timestamp UTC
    if dict(df.dtypes).get("Date") == "bigint":
        from pyspark.sql import functions as F
        df = df.withColumn("Date", F.timestamp_micros((F.col("Date") / 1000).cast("long")))

    # 4. Range partitioning berbasis Date & urutkan di dalam partisi (Date-clustered)
    df_partitioned = df.repartitionByRange(num_files, "Date").sortWithinPartitions("Date")

    t_start = time.perf_counter()

    # 5. Tulis ke Iceberg
    df_partitioned.writeTo(full_table_name).using("iceberg").tableProperty(
        "write.target-file-size-bytes", str(target_bytes)
    ).tableProperty(
        "write.parquet.row-group-size-bytes", str(ROW_GROUP_TARGET_BYTES)
    ).tableProperty(
        "write.parquet.compression-codec", COMPRESSION
    ).createOrReplace()

    t_end = time.perf_counter()
    wall_sec = t_end - t_start
    throughput = (210.0 / wall_sec) if wall_sec > 0 else 0.0

    logger.info(f"  Varian {tbl_short} berhasil dibuat dalam {wall_sec:.2f} detik ({throughput:.2f} MiB/s).")

    return {
        "variant": f"{target_mib:02d}mib",
        "target_file_size_mib": target_mib,
        "layout_build_wall_seconds": round(wall_sec, 2),
        "write_throughput_mib_s": round(throughput, 2),
        "generated_file_count": num_files,
        "table_name": tbl_short,
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }

def main():
    logger.info("=== H23: MEMULAI PEMBUATAN 4 VARIAN SECONDARY TABLE (AIS_SPEC) ===")
    if not SOURCE_PATH.exists():
        logger.error(f"Dataset sumber tidak ditemukan di {SOURCE_PATH}")
        sys.exit(1)

    spark = get_spark_session()
    results = []

    try:
        for target_mib in SECONDARY_GRID:
            res = build_secondary_variant(spark, target_mib)
            results.append(res)

        OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
            f.write("variant,target_file_size_mib,layout_build_wall_seconds,write_throughput_mib_s,generated_file_count,table_name,recorded_at\n")
            for r in results:
                f.write(f"{r['variant']},{r['target_file_size_mib']},{r['layout_build_wall_seconds']},{r['write_throughput_mib_s']},{r['generated_file_count']},{r['table_name']},{r['recorded_at']}\n")

        logger.info(f"Manifest biaya penulisan sekunder tersimpan di: {OUTPUT_MANIFEST}")
        logger.info("=== H23 STEP 2 SELESAI: 4 VARIAN AIS_SPEC BERHASIL DIBANGUN ===")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
