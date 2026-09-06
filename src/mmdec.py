"""Kontrak verifikasi MMDEC.

Seluruh angka di modul ini berasal dari artikel data:

    Averty, T., Nasios, I., Ray, C., Piliouras, N. (2026).
    MMDEC: Multimodal maritime dataset on the English channel.
    Data in Brief, 65, 112629. https://doi.org/10.1016/j.dib.2026.112629

Dataset: https://doi.org/10.5281/zenodo.17491518

Nilai-nilai ini dipakai sebagai acuan verifikasi snapshot (E0/G1), bukan
sebagai asumsi analisis.
"""
from datetime import date

DATA_ARTICLE_DOI = "10.1016/j.dib.2026.112629"
DATASET_DOI = "10.5281/zenodo.17491518"

# Periode observasi: 1 Juli - 30 September 2023.
OBSERVATION_START = date(2023, 7, 1)
OBSERVATION_END = date(2023, 9, 30)
OBSERVATION_DAYS = (OBSERVATION_END - OBSERVATION_START).days + 1  # 92
OBSERVATION_MINUTES = OBSERVATION_DAYS * 24 * 60

# Dataset_AIS_POS.parquet (tabel utama penelitian ini).
AIS_POS_ROWS = 19_014_229
AIS_POS_UNIQUE_MMSI = 25_130

# Tipe pesan posisi yang dipertahankan oleh kurator dataset.
# Ini menentukan kardinalitas GROUP BY pada Q3 (maksimal 6 grup).
AIS_POS_MESSAGE_TYPES = (1, 2, 3, 18, 19, 27)

# Kolom Dataset_AIS_POS.parquet menurut Tabel 2 artikel.
AIS_POS_COLUMNS = (
    "Date",
    "Source",
    "MessageType",
    "Mmsi",
    "NavigationStatus",
    "Latitude",
    "Longitude",
    "PositionAccuracy",
    "CourseOverGroundDegrees",
    "SpeedOverGround",
    "RateOfTurn",
    "TrueHeadingDegrees",
    "chunk_folder",
    "id_chunk",
)

# Kolom hasil kurasi (bukan field AIS asli). `id_chunk` bertipe daftar dan
# `chunk_folder` dapat NaN; keduanya harus dipertahankan apa adanya saat rewrite.
AIS_POS_CURATED_COLUMNS = ("chunk_folder", "id_chunk")

# Sentinel "tidak tersedia" menurut Tabel 2. Tidak boleh diperlakukan sebagai
# nilai numerik yang valid tanpa keputusan eksplisit yang dicatat.
AIS_POS_SENTINELS = {
    "CourseOverGroundDegrees": 511,
    "TrueHeadingDegrees": 511,
    "RateOfTurn": (128, -128),
}

# Tabel sekunder untuk robustness eksternal (E5).
SECONDARY_TABLES = {
    "Dataset_AIS_SPEC.parquet": {"rows": 13_558_007, "unique_mmsi": 23_958},
    "Dataset_BATHYMETRY.parquet": {"rows": 12_386_244},
}

# Vessel di AIS_POS yang tidak punya status message padanan.
VESSELS_WITHOUT_SPEC_MESSAGES = 1_172


def uniform_window_minutes(target_selectivity):
    """Lebar window `Date` (menit) untuk mencapai selectivity target
    ANDAI arrival rate seragam sepanjang 92 hari.

    Ini hanya alat sizing awal untuk E2. Trafik AIS nyata tidak seragam
    (lihat Fig. 5 artikel), sehingga boundary tetap wajib dikalibrasi dengan
    COUNT(*) dan yang dianalisis adalah measured selectivity.
    """
    if not 0 < target_selectivity <= 1:
        raise ValueError("target_selectivity harus berada di (0, 1]")
    return target_selectivity * OBSERVATION_MINUTES


def expected_matched_rows(target_selectivity, total_rows=AIS_POS_ROWS):
    """Perkiraan jumlah baris yang cocok pada selectivity target."""
    if not 0 < target_selectivity <= 1:
        raise ValueError("target_selectivity harus berada di (0, 1]")
    return int(round(target_selectivity * total_rows))
