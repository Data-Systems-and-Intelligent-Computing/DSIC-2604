"""
Test Source Contract and H1 Deliverables (Gate G1 Pre-check)
"""

import csv
import os
from pathlib import Path
import sys
import yaml

# Pastikan root proyek terdaftar di sys.path agar bisa dijalankan langsung
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.common import calculate_sha256, get_project_root


def test_protocol_freeze_exists():
    root = get_project_root()
    freeze_path = root / "configs" / "protocol_freeze.yaml"
    assert freeze_path.exists(), "configs/protocol_freeze.yaml harus ada pada H1"

    with open(freeze_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "research_questions" in data
    assert len(data["research_questions"]) == 5
    assert "hypotheses" in data
    assert len(data["hypotheses"]) == 5
    assert "novelty_boundary" in data
    print("  [OK] Uji 1: configs/protocol_freeze.yaml (RQ1-RQ5 & H1-H5) valid!")


def test_source_manifest_integrity():
    root = get_project_root()
    manifest_path = root / "data" / "manifests" / "source_manifest.csv"
    assert manifest_path.exists(), "data/manifests/source_manifest.csv harus ada pada H1"

    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 1, "source_manifest.csv minimal memiliki 1 entri dataset utama"
    primary = rows[0]

    assert primary["dataset_name"] == "Dataset_AIS_POS.parquet"
    assert primary["source_doi"] == "10.5281/zenodo.17491518"
    assert primary["paper_doi"] == "10.1016/j.dib.2026.112629"

    # Verifikasi file ada di disk dan cocok checksum-nya
    file_path = root / primary["file_path"]
    assert file_path.exists(), f"File dataset tidak ditemukan di {file_path}"

    actual_size = file_path.stat().st_size
    assert actual_size == int(primary["file_size_bytes"]), (
        f"Ukuran file tidak cocok: actual {actual_size} vs manifest {primary['file_size_bytes']}"
    )

    actual_hash = calculate_sha256(file_path)
    assert actual_hash == primary["sha256_checksum"], (
        f"Checksum SHA-256 tidak cocok: actual {actual_hash} vs manifest {primary['sha256_checksum']}"
    )
    print("  [OK] Uji 2: data/manifests/source_manifest.csv & Checksum SHA-256 cocok 100%!")


if __name__ == "__main__":
    print("=" * 60)
    print("[RUN] MENJALANKAN UJI INTEGRITAS HARI 1 (H1)")
    print("=" * 60)
    test_protocol_freeze_exists()
    test_source_manifest_integrity()
    print("=" * 60)
    print("[PASS] SEMUA UJI H1 LULUS DENGAN SEMPURNA!")
    print("=" * 60)
