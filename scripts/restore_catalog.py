"""Restore Iceberg catalog registration setelah container restart.

Iceberg REST Fixture (apache/iceberg-rest-fixture) bersifat in-memory:
semua registrasi schema dan tabel HILANG saat container restart.
Data fisik di MinIO tetap utuh. Script ini:
  1. Re-create schema  iceberg.dsic2604
  2. Re-register 4 tabel  ais_pos_{08,16,32,64}  ke catalog REST
     dengan menunjuk ke metadata file terbaru di MinIO.

Dijalankan kapan pun setelah stack di-restart:
    python scripts/restore_catalog.py

Prasyarat:
  - Docker stack sudah running  (docker compose ... up -d)
  - .env sudah dimuat (TRINO_HOST, TRINO_PORT, TRINO_USER, dll.)
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path

# ── pastikan root proyek ada di sys.path ──────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.common import get_project_root, load_yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── config ────────────────────────────────────────────────────────────────────

MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT",  "http://localhost:9000")
MINIO_USER      = os.getenv("MINIO_ROOT_USER",  "dsic2604")
MINIO_PASSWORD  = os.getenv("MINIO_ROOT_PASSWORD", "dsic2604desman")
MINIO_BUCKET    = os.getenv("MINIO_BUCKET",     "dsic2604")
WAREHOUSE_PATH  = "warehouse/dsic2604"          # path di dalam bucket

TRINO_HOST      = os.getenv("TRINO_HOST",   "localhost")
TRINO_PORT      = int(os.getenv("TRINO_PORT", "8080"))
TRINO_USER      = os.getenv("TRINO_USER",   "dsic2604")
CATALOG         = "iceberg"
SCHEMA          = "dsic2604"

TABLES = ["ais_pos_08", "ais_pos_16", "ais_pos_32", "ais_pos_64"]

# ── helpers ───────────────────────────────────────────────────────────────────

def minio_list(prefix: str) -> list[str]:
    """List object keys di MinIO bucket dengan prefix tertentu."""
    try:
        import boto3
        from botocore.client import Config
        s3 = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_USER,
            aws_secret_access_key=MINIO_PASSWORD,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        paginator = s3.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=MINIO_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys
    except ImportError:
        log.error("boto3 tidak terinstall. Jalankan: pip install boto3")
        sys.exit(1)


def latest_metadata_file(table_name: str) -> str:
    """Temukan file metadata Iceberg terbaru untuk sebuah tabel.

    Iceberg menamai metadata file sebagai  00000-<uuid>.metadata.json.
    File terbaru = yang terakhir secara leksikografis berdasarkan nama
    (konvensi Iceberg menjamin ini karena prefix numerik selalu naik).
    """
    prefix = f"{WAREHOUSE_PATH}/{table_name}/metadata/"
    keys = minio_list(prefix)
    meta_files = [
        k for k in keys
        if k.endswith(".metadata.json") and "/" + k.split("/")[-1] == "/" + k.split("/")[-1]
    ]
    if not meta_files:
        raise FileNotFoundError(
            f"Tidak ada .metadata.json di MinIO path: {prefix}"
        )
    # ambil basename lalu sort leksikografis
    basenames = sorted(k.split("/")[-1] for k in meta_files)
    return basenames[-1]   # terbaru


def trino_execute(sql: str):
    """Eksekusi query ke Trino via REST API (statement endpoint)."""
    headers = {
        "X-Trino-User": TRINO_USER,
        "Content-Type": "text/plain",
    }
    resp = requests.post(
        f"http://{TRINO_HOST}:{TRINO_PORT}/v1/statement",
        headers=headers,
        data=sql,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    # poll sampai query selesai
    while "nextUri" in data:
        resp = requests.get(data["nextUri"], headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

    if data.get("error"):
        raise RuntimeError(data["error"].get("message", str(data["error"])))

    return data


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Restore Iceberg Catalog (DSIC-2604) ===")

    # 1. Buat schema
    schema_location = f"s3://{MINIO_BUCKET}/{WAREHOUSE_PATH}"
    sql_schema = (
        f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA} "
        f"WITH (location = '{schema_location}')"
    )
    log.info(f"Creating schema: {CATALOG}.{SCHEMA}")
    trino_execute(sql_schema)
    log.info("  → Schema OK")

    # 2. Register tiap tabel
    for table in TABLES:
        table_location = f"s3://{MINIO_BUCKET}/{WAREHOUSE_PATH}/{table}"
        try:
            meta_file = latest_metadata_file(table)
        except FileNotFoundError as e:
            log.error(f"  [SKIP] {table}: {e}")
            continue

        log.info(f"Registering {table} → metadata: {meta_file}")
        sql_register = (
            f"CALL {CATALOG}.system.register_table("
            f"schema_name => '{SCHEMA}', "
            f"table_name  => '{table}', "
            f"table_location => '{table_location}', "
            f"metadata_file_name => '{meta_file}')"
        )
        try:
            trino_execute(sql_register)
            log.info(f"  → {table} registered OK")
        except RuntimeError as e:
            if "already exists" in str(e).lower():
                log.info(f"  → {table} already registered (skip)")
            else:
                log.error(f"  [ERROR] {table}: {e}")
                raise

    # 3. Verifikasi
    log.info("Verifying registered tables...")
    result = trino_execute(f"SHOW TABLES IN {CATALOG}.{SCHEMA}")
    registered = [
        row[0]
        for data_batch in [result]
        for row in data_batch.get("data", [])
    ]
    log.info(f"  Tables in catalog: {registered}")

    missing = [t for t in TABLES if t not in registered]
    if missing:
        log.error(f"FAILED: tabel berikut tidak terdaftar: {missing}")
        sys.exit(1)

    log.info("=== Catalog restored successfully. All 4 tables registered. ===")


if __name__ == "__main__":
    main()
