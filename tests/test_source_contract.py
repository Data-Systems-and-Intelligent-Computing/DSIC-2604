"""Kontrak verifikasi terhadap artikel data MMDEC (Data in Brief 65, 112629)."""
import pyarrow as pa

from src.mmdec import (
    AIS_POS_COLUMNS,
    AIS_POS_MESSAGE_TYPES,
    AIS_POS_ROWS,
    AIS_POS_UNIQUE_MMSI,
)
from src.validate_source import check_columns, check_date_type


def _schema(fields):
    return pa.schema(fields)


def test_article_constants():
    assert AIS_POS_ROWS == 19_014_229
    assert AIS_POS_UNIQUE_MMSI == 25_130
    # Q3 melakukan GROUP BY MessageType; kardinalitasnya maksimal 6.
    assert set(AIS_POS_MESSAGE_TYPES) == {1, 2, 3, 18, 19, 27}
    assert len(AIS_POS_COLUMNS) == 14


def test_full_schema_matches_article_table_2():
    fields = [(name, pa.string()) for name in AIS_POS_COLUMNS]
    fields[0] = ("Date", pa.timestamp("us"))
    schema = _schema(fields)
    report = check_columns(schema)
    assert report["missing"] == [] and report["extra"] == []
    assert check_date_type(schema)["is_temporal"]


def test_missing_column_is_reported():
    fields = [(n, pa.string()) for n in AIS_POS_COLUMNS if n != "SpeedOverGround"]
    report = check_columns(_schema(fields))
    assert report["missing"] == ["SpeedOverGround"]


def test_string_date_column_is_rejected():
    schema = _schema([("Date", pa.string()), ("Mmsi", pa.int64())])
    info = check_date_type(schema)
    assert not info["is_temporal"] and info["type"] == "string"
