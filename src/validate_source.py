"""Validate the canonical MMDEC AIS_POS snapshot (E0 / gate G1).

Kontrak angka dan kolom berasal dari artikel data MMDEC; lihat src/mmdec.py.
"""
import pyarrow.compute as pc
import pyarrow.parquet as pq

from src.common import sha256_file
from src.mmdec import (
    AIS_POS_COLUMNS,
    AIS_POS_ROWS,
    AIS_POS_UNIQUE_MMSI,
    DATASET_DOI,
)

# Dipertahankan untuk kompatibilitas pemanggil lama.
EXPECTED_ROWS = AIS_POS_ROWS
EXPECTED_UNIQUE_MMSI = AIS_POS_UNIQUE_MMSI

_TEMPORAL_PREFIXES = ("timestamp", "date32", "date64")


def _resolve(actual_names, expected):
    """Cocokkan nama kolom secara case-insensitive, kembalikan nama aktual."""
    lookup = {name.lower(): name for name in actual_names}
    return lookup.get(expected.lower())


def check_columns(schema):
    """Bandingkan schema terhadap Tabel 2 artikel."""
    actual = list(schema.names)
    missing = [c for c in AIS_POS_COLUMNS if _resolve(actual, c) is None]
    expected_lower = {c.lower() for c in AIS_POS_COLUMNS}
    extra = [c for c in actual if c.lower() not in expected_lower]
    return {"missing": missing, "extra": extra, "actual": actual}


def check_date_type(schema):
    """`Date` harus temporal agar predikat BETWEEN TIMESTAMP sah.

    Jika kolom bertipe string, seluruh kalibrasi selectivity dan pruning
    berbasis min/max statistics akan berperilaku berbeda; ini harus
    diselesaikan sebelum E1, bukan diselesaikan dengan cast di dalam query
    (cast menghalangi pruning dan mengubah konstruk yang diukur).
    """
    name = _resolve(schema.names, "Date")
    if name is None:
        return {"column": None, "type": None, "is_temporal": False}
    dtype = str(schema.field(name).type)
    return {
        "column": name,
        "type": dtype,
        "is_temporal": dtype.startswith(_TEMPORAL_PREFIXES),
    }


def count_unique_mmsi(path):
    """Hitung MMSI unik. Membaca satu kolom saja, tetap mahal pada 19M baris."""
    table = pq.read_table(path, columns=["Mmsi"])
    column = table.column(table.schema.names[0])
    return pc.count_distinct(column).as_py()


def validate_parquet(path, check_mmsi=True, checksum=True, strict=True):
    """Verifikasi snapshot sumber dan kembalikan record manifest.

    strict=True menaikkan ValueError pada pelanggaran kontrak; strict=False
    hanya melaporkan (berguna saat EDA awal sebelum snapshot final).
    """
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    columns = check_columns(schema)
    date_info = check_date_type(schema)

    result = {
        "path": str(path),
        "dataset_doi": DATASET_DOI,
        "rows": pf.metadata.num_rows,
        "row_groups": pf.metadata.num_row_groups,
        "columns": columns,
        "date_column": date_info,
        "unique_mmsi": count_unique_mmsi(path) if check_mmsi else None,
        "sha256": sha256_file(path) if checksum else None,
        "schema": str(schema),
        "violations": [],
    }

    if result["rows"] != AIS_POS_ROWS:
        result["violations"].append(
            f"row count {result['rows']:,} != {AIS_POS_ROWS:,} (artikel MMDEC)"
        )
    if columns["missing"]:
        result["violations"].append(f"kolom hilang: {columns['missing']}")
    if not date_info["is_temporal"]:
        result["violations"].append(
            f"kolom Date bertipe {date_info['type']!r}, bukan tipe temporal"
        )
    if check_mmsi and result["unique_mmsi"] != AIS_POS_UNIQUE_MMSI:
        result["violations"].append(
            f"MMSI unik {result['unique_mmsi']:,} != {AIS_POS_UNIQUE_MMSI:,} (artikel MMDEC)"
        )

    if strict and result["violations"]:
        raise ValueError(
            "Snapshot tidak sesuai kontrak MMDEC:\n  - "
            + "\n  - ".join(result["violations"])
        )
    return result
