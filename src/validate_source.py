"""
Validasi Gate G1 : Kontrak Integritas Dataset MMDEC (Data In Brief, 2026)
DSIC-2604 : Verifikasi deterministik sebelum partitioning.
"""
from pathlib import Path # Mengelola path direktori/file berbasis objek (OOP).
import hashlib # Membuat hash SHA256 untuk verifikasi integritas file (File Fingerprint).
import json # Mengolah file JSON (konfigurasi metadata).
import sys # Mengakses parameter baris perintah dan exit interpreter.
import pyarrow.parquet as pq  # Membaca format Parquet tanpa memuat seluruh dataset ke RAM.
import duckdb # Mengakses DuckDB (engine analitik in-memory) untuk menjalankan kueri SQL cepat.


# Path file sumber dan output laporan
SOURCE_PATH = Path("Dataset/Dataset_AIS_POS.parquet")
REPORT_PATH = Path("data/manifests/gate_g1_validation_report.json")


# Nilai ground-truth resmi dari paper MMDEC (Table 2 & metadata)
EXPECTED_SHA256 = "88998c43f7e152710c3b157cf47c8119cdef05554d2a6d32e980ce36101b5785"
EXPECTED_ROW_COUNT = 19_014_229
EXPECTED_NUM_COLUMNS = 14
EXPECTED_DISTINCT_MMSI = 25_130

def check_sha256(file_path: Path, expected_hash: str) -> bool:
    """Menghitung hash SHA-256 berkas fisik secara streaming (chunk-by-chunk)."""
    print(f"[1/3] Memeriksa Integritas Berkas Fisik: {file_path.name}...")
    
    if not file_path.exists():
        print(f"      [GAGAL] File {file_path} tidak ditemukan!")
        return False

    sha256_hash = hashlib.sha256()
    # Baca file per blok 1 MB agar tidak membebani memori RAM
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(1024 * 1024), b""):
            sha256_hash.update(byte_block)

    actual_hash = sha256_hash.hexdigest()
    print(f"      - SHA-256 Aktual    : {actual_hash}")
    print(f"      - SHA-256 Ekspektasi: {expected_hash}")

    if actual_hash.lower() == expected_hash.lower():
        print("      [LULUS] Checksum SHA-256 identik 100% dengan acuan publik.")
        return True
    else:
        print("      [GAGAL] Checksum tidak cocok! File terindikasi rusak atau berbeda versi.")
        return False

def check_parquet_metadata(file_path: Path) -> bool:
    """Memverifikasi skema kolom dan metadata baris menggunakan PyArrow."""
    print(f"\n[2/3] Memeriksa Metadata Parquet (PyArrow): {file_path.name}...")

    # Membaca footer Parquet tanpa membaca seluruh isi data ke memori
    pq_file = pq.ParquetFile(file_path)
    metadata = pq_file.metadata
    schema = pq_file.schema_arrow

    num_rows = metadata.num_rows
    num_cols = metadata.num_columns
    num_row_groups = metadata.num_row_groups

    print(f"      - Jumlah Baris Metadata : {num_rows:,} baris")
    print(f"      - Jumlah Kolom          : {num_cols} kolom")
    print(f"      - Jumlah Row Groups     : {num_row_groups} grup")

    # 14 kolom resmi sesuai Tabel 2 artikel MMDEC (Dataset_AIS_POS)
    expected_columns = [
        "Date", "Source", "MessageType", "Mmsi", "NavigationStatus",
        "Latitude", "Longitude", "PositionAccuracy", "CourseOverGroundDegrees",
        "SpeedOverGround", "RateOfTurn", "TrueHeadingDegrees",
        "chunk_folder", "id_chunk"
    ]

    actual_columns = [field.name for field in schema]

    is_row_valid = (num_rows == EXPECTED_ROW_COUNT)
    is_col_valid = (num_cols == EXPECTED_NUM_COLUMNS)
    # Periksa apakah semua 14 kolom wajib hadir tanpa terikat urutan kaku
    is_schema_valid = (set(actual_columns) == set(expected_columns))


    if is_row_valid and is_col_valid and is_schema_valid:
        print("      [LULUS] Struktur skema 14 kolom & jumlah baris metadata cocok persis.")
        return True
    else:
        print(f"      [GAGAL] Ketidaksesuaian terdeteksi:")
        if not is_row_valid:
            print(f"        * Baris: Ditemukan {num_rows:,}, Ekspektasi {EXPECTED_ROW_COUNT:,}")
        if not is_col_valid or not is_schema_valid:
            print(f"        * Kolom: Ditemukan {actual_columns}") 
        return False
 
def check_semantic_contract(file_path: Path) -> dict:
    """Memeriksa kebenaran isi data (MMSI unik, rentang tanggal, dsb.) dengan DuckDB."""
    print(f"\n[3/3] Memeriksa Kontrak Semantik Data (DuckDB): {file_path.name}...")

    # Konversi path ke format string yang kompatibel untuk query SQL
    parquet_target = str(file_path).replace("\\", "/")

    con = duckdb.connect()

    # Menjalankan query agregasi langsung di atas file Parquet
    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT Mmsi) AS total_mmsi,
            MIN(Date) AS min_date,
            MAX(Date) AS max_date,
            COUNT(DISTINCT CAST(Date AS DATE)) AS distinct_days
        FROM read_parquet('{parquet_target}')
    """
    print("      - Menjalankan agregasi analitis pada 19M+ baris...")
    result = con.execute(query).fetchone()

    total_rows, total_mmsi, min_date, max_date, distinct_days = result

    print(f"      - Total Baris Terbaca : {total_rows:,} (Ekspektasi: {EXPECTED_ROW_COUNT:,})")
    print(f"      - Kapal Unik (MMSI)   : {total_mmsi:,} (Ekspektasi: {EXPECTED_DISTINCT_MMSI:,})")
    print(f"      - Rentang Waktu       : {min_date} s.d. {max_date}")
    print(f"      - Jumlah Hari Kalender: {distinct_days} hari")

    # Evaluasi kecocokan dengan kontrak
    valid_rows = (total_rows == EXPECTED_ROW_COUNT)
    valid_mmsi = (total_mmsi == EXPECTED_DISTINCT_MMSI)
    is_passed = valid_rows and valid_mmsi

    if is_passed:
        print("      [LULUS] Kontrak semantik dan integritas nilai data 100% valid.")
    else:
        print("      [GAGAL] Data semantik tidak sesuai kontrak publik paper.")

    return {
        "total_rows": total_rows,
        "total_mmsi": total_mmsi,
        "min_date": str(min_date),
        "max_date": str(max_date),
        "distinct_days": distinct_days,
        "is_passed": is_passed
    }

def main():
    print("=" * 70)
    print("DSIC-2604: AUDIT INTEGRITAS DATASET SUMBER MMDEC (GATE G1)")
    print("=" * 70)

    # Pastikan folder output laporan sudah ada
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Jalankan Pengecekan Checksum
    pass_sha = check_sha256(SOURCE_PATH, EXPECTED_SHA256)

    # 2. Jalankan Pengecekan Metadata Parquet
    pass_meta = check_parquet_metadata(SOURCE_PATH)

    # 3. Jalankan Pengecekan Semantik Data
    sem_res = check_semantic_contract(SOURCE_PATH)
    pass_sem = sem_res["is_passed"]

    # Evaluasi Hasil Keseluruhan Gate G1
    all_passed = pass_sha and pass_meta and pass_sem

    print("\n" + "=" * 70)
    if all_passed:
        print("[SUKSES] GATE G1 LULUS 100%! Dataset siap untuk tahap eksperimen.")
    else:
        print("[GAGAL] GATE G1 GAGAL! Dataset tidak memenuhi kontrak acuan.")
    print("=" * 70)

    # Simpan hasil audit ke file JSON untuk bukti empiris
    report_data = {
        "gate": "G1",
        "dataset_path": str(SOURCE_PATH),
        "status": "PASSED" if all_passed else "FAILED",
        "checks": {
            "checksum_sha256": "PASSED" if pass_sha else "FAILED",
            "parquet_metadata": "PASSED" if pass_meta else "FAILED",
            "semantic_contract": "PASSED" if pass_sem else "FAILED"
        },
        "semantic_metrics": sem_res
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"Laporan audit Gate G1 berhasil disimpan di: {REPORT_PATH}\n")

    # Keluar dengan kode 0 (sukses) atau 1 (gagal)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
