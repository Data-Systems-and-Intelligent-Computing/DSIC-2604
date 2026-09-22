"""Membekukan data mentah hasil benchmark dan menghitung SHA-256 snapshot (H12).

Tahapan yang dilakukan:
1. Menyalin results/raw/runs.jsonl menjadi results/raw/runs_frozen.jsonl secara aman.
2. Menghitung sidik jari SHA-256 Checksum dari file beku tersebut.
3. Memvalidasi baris data (harus tepat 1.584 baris).
4. Menyimpan bukti pembekuan ke data/manifests/raw_freeze_manifest.json.
"""
import sys
import json
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

SRC_LOG = Path("results/raw/runs.jsonl")
FROZEN_LOG = Path("results/raw/runs_frozen.jsonl")
MANIFEST_OUTPUT = Path("data/manifests/raw_freeze_manifest.json")

def calculate_sha256(filepath: Path) -> str:
    """Menghitung SHA-256 secara streaming (blok 64 KB)."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def freeze_raw_data():
    log.info("=== H12: FREEZE RAW DATA & SNAPSHOT CHECKSUM ===")

    if not SRC_LOG.exists():
        log.error(f"File log mentah tidak ditemukan: {SRC_LOG}")
        sys.exit(1)

    # 1. Salin file menjadi runs_frozen.jsonl
    log.info(f"1. Membekukan file data mentah...")
    shutil.copy2(SRC_LOG, FROZEN_LOG)
    log.info(f"   -> Berhasil disalin ke: {FROZEN_LOG}")

    # 2. Hitung jumlah baris & ukuran fisik
    with open(FROZEN_LOG, "r", encoding="utf-8") as f:
        line_count = sum(1 for line in f if line.strip())

    file_size_bytes = FROZEN_LOG.stat().st_size
    log.info(f"2. Ukuran fisik: {file_size_bytes:,} bytes | Total baris: {line_count:,} baris")

    if line_count != 1584:
        log.error(f"FATAL: Jumlah baris data tidak cocok! Ditemukan {line_count}, seharusnya 1584.")
        sys.exit(1)

    # 3. Hitung SHA-256 Checksum
    log.info("3. Menghitung sidik jari SHA-256 Checksum...")
    sha256_hash = calculate_sha256(FROZEN_LOG)
    log.info(f"   -> SHA-256: {sha256_hash}")

    # 4. Buat manifest deliverable resmi
    freeze_manifest = {
        "milestone": "H12_RAW_DATA_FREEZE",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(SRC_LOG),
        "frozen_file": str(FROZEN_LOG),
        "file_size_bytes": file_size_bytes,
        "line_count": line_count,
        "expected_runs": 1584,
        "sha256_checksum": sha256_hash,
        "freeze_status": "FROZEN_AND_VERIFIED",
        "next_step": "Minggu 3 (Analisis, Visualisasi, dan Uji Hipotesis)"
    }

    MANIFEST_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUTPUT.write_text(json.dumps(freeze_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"4. Manifest pembekuan resmi tersimpan di: {MANIFEST_OUTPUT}")

    print()
    print("=" * 60)
    print("STATUS H12: DATA MENTAH RESMI DIBEKUKAN (RAW DATA FROZEN)")
    print(f"  File Beku (Frozen) : {FROZEN_LOG}")
    print(f"  Total Baris Data   : {line_count}/1584 (Lengkap 100%)")
    print(f"  Ukuran File        : {file_size_bytes:,} bytes")
    print(f"  SHA-256 Checksum   : {sha256_hash}")
    print(f"  Manifest Bukti     : {MANIFEST_OUTPUT}")
    print("=" * 60)

if __name__ == "__main__":
    freeze_raw_data()
