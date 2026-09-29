#!/usr/bin/env python3
"""
DSIC-2604: H23 — Unduh & Validasi Integritas Secondary Dataset (Dataset_AIS_SPEC.parquet)
========================================================================================
Sumber: Zenodo MMDEC (DOI: 10.5281/zenodo.17491518)
Paper acuan: Averty et al. (Data in Brief, 2026)
Expected:
  - Rows: 13,558,007
  - Size: 209,957,042 bytes
  - MD5:  f1dd53064868fa078c714986991c3941
"""

import hashlib
import logging
import os
import sys
import time
from pathlib import Path
import pyarrow.parquet as pq
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("H23-Downloader")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "Dataset"
DEST_PATH = DATASET_DIR / "Dataset_AIS_SPEC.parquet"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "source_manifest.csv"

ZENODO_URL = "https://zenodo.org/api/records/17491518/files/Dataset_AIS_SPEC.parquet/content"
EXPECTED_SIZE = 209957042
EXPECTED_MD5 = "f1dd53064868fa078c714986991c3941"
EXPECTED_ROWS = 13558007
EXPECTED_MMSI = 23958

def download_file(url: str, dest: Path, expected_size: int):
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest.with_suffix(".parquet.tmp")

    if dest.exists() and dest.stat().st_size == expected_size:
        logger.info(f"File {dest.name} sudah ada dengan ukuran tepat ({expected_size} bytes). Melewati unduhan.")
        return

    logger.info(f"Mengunduh {dest.name} dari Zenodo ({expected_size / (1024*1024):.2f} MiB)...")
    t0 = time.time()
    
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        downloaded = 0
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024): # 1 MiB chunk
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = (downloaded / expected_size) * 100.0
                    mb = downloaded / (1024 * 1024)
                    speed = mb / max(time.time() - t0, 0.001)
                    print(f"\r  Progres: {mb:.1f}/{expected_size/(1024*1024):.1f} MiB ({pct:.1f}%) | {speed:.2f} MiB/s", end="", flush=True)

    print()
    temp_path.replace(dest)
    logger.info(f"Unduhan selesai dalam {time.time() - t0:.1f} detik: {dest}")

def verify_checksums(file_path: Path):
    logger.info(f"Memverifikasi Checksum (MD5 & SHA-256) untuk {file_path.name}...")
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(2 * 1024 * 1024), b""):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

    actual_md5 = md5_hash.hexdigest().lower()
    actual_sha256 = sha256_hash.hexdigest().lower()

    logger.info(f"  MD5 Aktual    : {actual_md5}")
    logger.info(f"  MD5 Ekspektasi: {EXPECTED_MD5}")
    logger.info(f"  SHA-256 Aktual: {actual_sha256}")

    if actual_md5 != EXPECTED_MD5.lower():
        raise ValueError(f"MD5 tidak cocok! File terindikasi korup. ({actual_md5} != {EXPECTED_MD5})")

    logger.info("  [PASSED] Checksum MD5 cocok 100% dengan Zenodo.")
    return actual_sha256

def verify_parquet_metadata(file_path: Path):
    logger.info(f"Memverifikasi struktur internal Parquet: {file_path.name}...")
    pf = pq.ParquetFile(file_path)
    meta = pf.metadata
    logger.info(f"  Jumlah baris    : {meta.num_rows:,} (Ekspektasi: {EXPECTED_ROWS:,})")
    logger.info(f"  Jumlah kolom    : {meta.num_columns}")
    logger.info(f"  Jumlah row group: {meta.num_row_groups}")

    if meta.num_rows != EXPECTED_ROWS:
        raise ValueError(f"Jumlah baris ({meta.num_rows}) tidak sesuai ground-truth ({EXPECTED_ROWS})!")

    logger.info("  [PASSED] Metadata baris Parquet 100% terverifikasi.")

def update_source_manifest(sha256_hex: str):
    if not MANIFEST_PATH.exists():
        logger.warning("source_manifest.csv tidak ditemukan.")
        return

    content = MANIFEST_PATH.read_text(encoding="utf-8")
    if "Dataset_AIS_SPEC.parquet" in content:
        logger.info("Dataset_AIS_SPEC.parquet sudah tercatat di source_manifest.csv.")
        return

    entry = (
        f"Dataset_AIS_SPEC.parquet,secondary_benchmark,10.5281/zenodo.17491518,"
        f"10.1016/j.dib.2026.112629,CC-BY-NC-4.0,{time.strftime('%Y-%m-%d')},"
        f"Dataset/Dataset_AIS_SPEC.parquet,{EXPECTED_SIZE},{sha256_hex},"
        f"{EXPECTED_ROWS},{EXPECTED_MMSI},VERIFIED_H23\n"
    )
    with open(MANIFEST_PATH, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info(f"Berhasil memperbarui {MANIFEST_PATH.name} dengan rekaman Dataset_AIS_SPEC.parquet.")

def main():
    logger.info("=== H23: DOWNLOAD & VERIFY SECONDARY DATASET ===")
    download_file(ZENODO_URL, DEST_PATH, EXPECTED_SIZE)
    sha256_hex = verify_checksums(DEST_PATH)
    verify_parquet_metadata(DEST_PATH)
    update_source_manifest(sha256_hex)
    logger.info("=== H23 STEP 1 SELESAI: DATASET SEKUNDER TERSEDIA & TERVERIFIKASI ===")

if __name__ == "__main__":
    main()
