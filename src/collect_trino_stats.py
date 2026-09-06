"""Normalize Trino telemetry without changing engine semantics.

Never equate split count with file count.
Never call physical input bytes 'network bytes' without verification.

Trino REST (`/v1/query/{queryId}`) menyerialkan Duration dan DataSize sebagai
string berformat, misalnya "1.23s" dan "45.6MB", bukan angka. Klien lain
(mis. `trino` Python client) dapat mengembalikan varian bernama *Millis/*Bytes.
Kedua bentuk ditangani di sini; kegagalan parsing menghasilkan None yang
eksplisit, bukan nol diam-diam.
"""
import re

_DURATION_UNITS_MS = {
    "ns": 1e-6,
    "us": 1e-3,
    "ms": 1.0,
    "s": 1e3,
    "m": 60e3,
    "h": 3600e3,
    "d": 86400e3,
}

# Trino memakai satuan desimal (kB = 1000) pada DataSize.
_SIZE_UNITS_BYTES = {
    "B": 1,
    "kB": 10**3,
    "MB": 10**6,
    "GB": 10**9,
    "TB": 10**12,
    "PB": 10**15,
}

_NUM = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([A-Za-z]+)\s*$")


def parse_duration_ms(value):
    """'1.23s' -> 1230.0 ; 45 -> 45.0 ; None -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = _NUM.match(str(value))
    if not m:
        return None
    magnitude, unit = float(m.group(1)), m.group(2)
    factor = _DURATION_UNITS_MS.get(unit)
    return magnitude * factor if factor is not None else None


def parse_data_size_bytes(value):
    """'45.6MB' -> 45600000.0 ; 1024 -> 1024.0 ; None -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = _NUM.match(str(value))
    if not m:
        return None
    magnitude, unit = float(m.group(1)), m.group(2)
    for key, factor in _SIZE_UNITS_BYTES.items():
        if unit.lower() == key.lower():
            return magnitude * factor
    return None


def _first(stats, *names):
    for name in names:
        if name in stats and stats[name] is not None:
            return stats[name]
    return None


def normalize_query_info(info):
    """Ubah QueryInfo Trino menjadi record datar untuk raw run log."""
    stats = info.get("queryStats", info.get("stats", {})) or {}

    record = {
        "query_id": info.get("queryId", info.get("id")),
        "state": info.get("state"),
        "elapsed_ms": parse_duration_ms(
            _first(stats, "elapsedTime", "elapsedTimeMillis")
        ),
        "queued_ms": parse_duration_ms(
            _first(stats, "queuedTime", "queuedTimeMillis")
        ),
        "planning_ms": parse_duration_ms(
            _first(stats, "planningTime", "planningTimeMillis")
        ),
        "cpu_ms": parse_duration_ms(
            _first(stats, "totalCpuTime", "totalCpuTimeMillis", "cpuTimeMillis")
        ),
        "physical_input_bytes": parse_data_size_bytes(
            _first(stats, "physicalInputDataSize", "physicalInputDataSizeBytes")
        ),
        "physical_input_rows": _first(stats, "physicalInputPositions"),
        "processed_input_bytes": parse_data_size_bytes(
            _first(stats, "processedInputDataSize", "processedInputDataSizeBytes")
        ),
        "processed_input_rows": _first(
            stats, "processedInputPositions", "processedRows"
        ),
        "completed_splits": _first(stats, "completedSplits"),
        "total_splits": _first(stats, "totalSplits"),
        "peak_memory_bytes": parse_data_size_bytes(
            _first(
                stats,
                "peakUserMemoryReservation",
                "peakMemoryBytes",
                "peakUserMemoryBytes",
            )
        ),
    }

    # Gate G6 mensyaratkan metrik ini benar-benar ada. Telemetry yang diam-diam
    # kosong adalah mode kegagalan yang harus terlihat, bukan disembunyikan.
    record["missing_metrics"] = [
        key
        for key in (
            "elapsed_ms",
            "cpu_ms",
            "physical_input_bytes",
            "processed_input_rows",
            "completed_splits",
            "peak_memory_bytes",
        )
        if record[key] is None
    ]
    return record
