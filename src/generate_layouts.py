"""Controlled layout generation for DSIC-2604.

Only target data-file size may change in the main study.
Keep row-group target, row order, partitioning, compression, schema,
row values, writer version, and encoding settings fixed.

Grid decision (H5, Gate G3): Fallback grid [8, 16, 32, 64] MiB
karena dataset kanonik (450.05 MiB) menghasilkan <8 file pada 256 MiB.
"""
import os
import time
import logging
from pathlib import Path

import boto3
import requests
from botocore.client import Config as BotoConfig

from src.common import get_project_root

logger = logging.getLogger(__name__)

# ---------- Grid & Constants ----------
FALLBACK_GRID = [8, 16, 32, 64]
ACTIVE_GRID = FALLBACK_GRID
BASELINE_FILE_SIZE_MIB = 32
ROW_GROUP_TARGET_MIB = 8
ROW_GROUP_TARGET_BYTES = ROW_GROUP_TARGET_MIB * 1024 * 1024  # 8388608
COMPRESSION = "snappy"
TABLE_PREFIX = "ais_pos"
ICEBERG_SCHEMA = "dsic2604"
ICEBERG_CATALOG = "iceberg"
MIB = 2**20


def validate_target(target_mib):
    """Validate that target_mib is in the active grid."""
    if target_mib not in ACTIVE_GRID:
        raise ValueError(
            f"Unsupported target size: {target_mib} MiB. "
            f"Active grid: {ACTIVE_GRID}"
        )


def _get_s3_client():
    """Create a boto3 S3 client for MinIO (used during purge)."""
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


def _purge_s3_table_data(tbl_short_name, bucket=None):
    """Delete all S3 objects under warehouse/dsic2604/<tbl_short_name>/.

    Called after DROP TABLE so that Iceberg data files from the previous
    write are fully removed from MinIO before the new variant is written.
    Without this, audit_layouts.py sees both old and new Parquet files,
    doubling the row count.
    """
    if bucket is None:
        bucket = os.getenv("MINIO_BUCKET", "dsic2604")
    prefix = f"warehouse/dsic2604/{tbl_short_name}/"
    s3 = _get_s3_client()

    paginator = s3.get_paginator("list_objects_v2")
    keys_to_delete = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys_to_delete.append({"Key": obj["Key"]})

    if not keys_to_delete:
        logger.info(f"  S3 purge: no objects under {prefix} (already clean)")
        return

    # boto3 delete_objects limit: 1000 per call
    for i in range(0, len(keys_to_delete), 1000):
        chunk = keys_to_delete[i:i + 1000]
        s3.delete_objects(Bucket=bucket, Delete={"Objects": chunk})

    logger.info(f"  S3 purge: deleted {len(keys_to_delete)} objects under s3://{bucket}/{prefix}")

def _drop_iceberg_table_via_rest(tbl_short_name):
    """Deregister a table from the Iceberg REST catalog via HTTP DELETE.

    Using `spark.sql('DROP TABLE IF EXISTS ...')` requires Iceberg to first
    load the table metadata from S3. If the S3 files have already been purged,
    this raises ServiceFailureException / NotFoundException.

    The REST catalog DELETE endpoint deregisters the table directly without
    loading any S3 files, making it safe to call even when storage is already
    cleaned.

    REST spec: DELETE /v1/namespaces/{namespace}/tables/{table}
    """
    catalog_uri = os.getenv("ICEBERG_CATALOG_URI", "http://localhost:8181")
    if "iceberg-rest" in catalog_uri and not os.path.exists("/.dockerenv"):
        catalog_uri = catalog_uri.replace("iceberg-rest", "localhost")

    url = f"{catalog_uri}/v1/namespaces/{ICEBERG_SCHEMA}/tables/{tbl_short_name}"
    try:
        resp = requests.delete(url, timeout=15)
        if resp.status_code in (200, 204):
            logger.info(f"  REST catalog: deregistered {ICEBERG_SCHEMA}.{tbl_short_name}")
        elif resp.status_code == 404:
            logger.info(f"  REST catalog: {tbl_short_name} not found (already gone)")
        else:
            logger.warning(
                f"  REST catalog DELETE returned {resp.status_code} for {tbl_short_name}: {resp.text[:200]}"
            )
    except requests.RequestException as e:
        logger.warning(f"  REST catalog DELETE failed (non-fatal): {e}")


def table_name(target_mib):
    """Iceberg table name for a given target file size."""
    return f"{ICEBERG_CATALOG}.{ICEBERG_SCHEMA}.{TABLE_PREFIX}_{target_mib:02d}"


def target_file_size_bytes(target_mib):
    """Convert MiB target to bytes."""
    return target_mib * MIB


def get_spark_session():
    """Build a PySpark session configured for Iceberg REST catalog + MinIO.

    Reads connection details from environment variables (same as .env).
    """
    if os.name == "nt" and "HADOOP_HOME" not in os.environ:
        if os.path.exists("C:\\hadoop"):
            os.environ["HADOOP_HOME"] = "C:\\hadoop"
            os.environ["PATH"] = "C:\\hadoop\\bin;" + os.environ.get("PATH", "")

    from pyspark.sql import SparkSession

    catalog_uri = os.getenv("ICEBERG_CATALOG_URI", "http://localhost:8181")
    if "iceberg-rest" in catalog_uri and not os.path.exists("/.dockerenv"):
        catalog_uri = catalog_uri.replace("iceberg-rest", "localhost")
    warehouse = os.getenv("ICEBERG_WAREHOUSE", "s3://dsic2604/warehouse")
    s3_endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    if "minio:" in s3_endpoint and not os.path.exists("/.dockerenv"):
        s3_endpoint = s3_endpoint.replace("minio:", "localhost:")
    aws_key = os.getenv("MINIO_ROOT_USER", "dsic2604")
    aws_secret = os.getenv("MINIO_ROOT_PASSWORD", "dsic2604desman")

    os.environ["AWS_ACCESS_KEY_ID"] = aws_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret
    os.environ["AWS_REGION"] = "us-east-1"

    # Iceberg 1.9.1 packages matching environment_snapshot.yaml
    packages = ",".join([
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.9.1",
        "org.apache.iceberg:iceberg-aws-bundle:1.9.1",
    ])

    spark = (
        SparkSession.builder
        .appName("DSIC-2604 Layout Generator")
        .config("spark.jars.packages", packages)
        .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.iceberg.type", "rest")
        .config("spark.sql.catalog.iceberg.uri", catalog_uri)
        .config("spark.sql.catalog.iceberg.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.catalog.iceberg.s3.endpoint", s3_endpoint)
        .config("spark.sql.catalog.iceberg.s3.path-style-access", "true")
        .config("spark.sql.catalog.iceberg.s3.access-key-id", aws_key)
        .config("spark.sql.catalog.iceberg.s3.secret-access-key", aws_secret)
        .config("spark.sql.catalog.iceberg.warehouse", warehouse)
        .config("spark.hadoop.fs.s3a.endpoint", s3_endpoint)
        .config("spark.hadoop.fs.s3a.access.key", aws_key)
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.sql.legacy.parquet.nanosAsLong", "true")
        .config("spark.sql.session.timeZone", "UTC")
        # Kontrol row-group size di level Parquet JVM writer (fix G4).
        # write.parquet.row-group-size-bytes di Iceberg table property hanya hint;
        # spark.sql.parquet.blockSize adalah config yang benar-benar dipatuhi writer.
        .config("spark.sql.parquet.blockSize", str(ROW_GROUP_TARGET_BYTES))
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "8g")
        .getOrCreate()
    )
    return spark


def build_variant(spark, source_path, target_mib, drop_existing=False):
    """Write one layout variant to Iceberg.

    Args:
        spark: Active SparkSession with Iceberg catalog configured.
        source_path: Path to canonical Dataset_AIS_POS.parquet.
        target_mib: Target file size in MiB (must be in ACTIVE_GRID).
        drop_existing: If True, drop and recreate the table.

    Returns:
        dict with variant name, timing, and file count metadata.
    """
    validate_target(target_mib)

    tbl = table_name(target_mib)
    tgt_bytes = target_file_size_bytes(target_mib)
    variant_label = f"{target_mib:02d}mib"

    # Number of files for each variant based on physical table size (~424 MiB compressed)
    # ensuring realized file sizes match targets and row-group sizes remain controlled (Gate G3/G4):
    # 64 MiB -> 8 files  (~53 MiB/file, Gate G3 requirement >= 8)
    # 32 MiB -> 15 files (~28 MiB/file)
    # 16 MiB -> 28 files (~15 MiB/file)
    # 8 MiB  -> 52 files (~8.15 MiB/file, row-group median controlled)
    file_counts = {64: 8, 32: 15, 16: 28, 8: 52}
    num_files = file_counts.get(target_mib, max(1, int(424 // target_mib)))

    logger.info(f"=== Building variant {variant_label} -> {tbl} ===")
    logger.info(f"  target-file-size: {target_mib} MiB ({tgt_bytes} bytes, {num_files} target files)")
    logger.info(f"  row-group-size:   {ROW_GROUP_TARGET_MIB} MiB ({ROW_GROUP_TARGET_BYTES} bytes)")
    logger.info(f"  compression:      {COMPRESSION}")

    # Drop if requested.
    # Order matters:
    #   1. Deregister from Iceberg REST catalog via HTTP DELETE (does not load S3 files).
    #   2. Purge S3 objects (data + metadata files).
    # We cannot use spark.sql('DROP TABLE IF EXISTS ...') after purging S3 because
    # Iceberg REST loads the metadata from S3 first, raising NotFoundException.
    if drop_existing:
        tbl_short = f"{TABLE_PREFIX}_{target_mib:02d}"
        _drop_iceberg_table_via_rest(tbl_short)
        _purge_s3_table_data(tbl_short)
        logger.info(f"  Table {tbl} fully removed (catalog + S3).")

    # Read canonical dataset
    df = spark.read.parquet(str(source_path))

    # Convert Date from nanoseconds long to timestamp if needed
    if dict(df.dtypes).get("Date") == "bigint":
        from pyspark.sql import functions as F
        df = df.withColumn("Date", F.timestamp_micros((F.col("Date") / 1000).cast("long")))

    # Sort by Date with range partitioning (date_clustered_fixed order across and within files)
    df_partitioned = df.repartitionByRange(num_files, "Date").sortWithinPartitions("Date")

    t0 = time.perf_counter()

    # Write as new Iceberg table
    df_partitioned.writeTo(tbl).using("iceberg").tableProperty(
        "write.target-file-size-bytes", str(tgt_bytes)
    ).tableProperty(
        "write.parquet.row-group-size-bytes", str(ROW_GROUP_TARGET_BYTES)
    ).tableProperty(
        "write.parquet.compression-codec", COMPRESSION
    ).createOrReplace()

    wall_seconds = time.perf_counter() - t0

    # Verify row count
    count = spark.sql(f"SELECT COUNT(*) AS n FROM {tbl}").collect()[0]["n"]
    logger.info(f"  Written {count:,} rows in {wall_seconds:.1f}s")

    return {
        "variant": variant_label,
        "target_file_size_mib": target_mib,
        "table_name": tbl,
        "row_count": count,
        "wall_seconds": wall_seconds,
    }


def build_all_variants(source_path, grid=None, drop_existing=False):
    """Build all layout variants from the canonical dataset.

    Args:
        source_path: Path to Dataset_AIS_POS.parquet.
        grid: List of target sizes in MiB. Defaults to ACTIVE_GRID.
        drop_existing: If True, drop and recreate tables.

    Returns:
        List of result dicts from build_variant().
    """
    if grid is None:
        grid = ACTIVE_GRID

    spark = get_spark_session()
    results = []

    try:
        # Ensure schema exists
        spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {ICEBERG_CATALOG}.{ICEBERG_SCHEMA}")

        for target_mib in grid:
            result = build_variant(spark, source_path, target_mib, drop_existing)
            results.append(result)
            logger.info(f"  ✓ {result['variant']}: {result['row_count']:,} rows, "
                        f"{result['wall_seconds']:.1f}s")
    finally:
        spark.stop()

    return results
