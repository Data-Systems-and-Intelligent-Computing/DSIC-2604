"""Calibrate Date windows to measured selectivity (E2).

Yang dianalisis selalu measured selectivity, bukan label target.
"""
from dataclasses import dataclass

from src.mmdec import expected_matched_rows, uniform_window_minutes

# Toleransi penerimaan band: |measured - target| / target.
DEFAULT_BAND_TOLERANCE = 0.20


@dataclass(frozen=True)
class SelectivityBand:
    target: float
    start_ts: str
    end_ts: str
    matched_rows: int
    total_rows: int

    @property
    def measured(self):
        return measured_selectivity(self.matched_rows, self.total_rows)

    @property
    def relative_error(self):
        return abs(self.measured - self.target) / self.target

    def accepted(self, tolerance=DEFAULT_BAND_TOLERANCE):
        return self.relative_error <= tolerance


def measured_selectivity(matched_rows, total_rows):
    if total_rows <= 0:
        raise ValueError("total_rows must be positive")
    if matched_rows < 0:
        raise ValueError("matched_rows must be non-negative")
    if matched_rows > total_rows:
        raise ValueError("matched_rows tidak boleh melebihi total_rows")
    return matched_rows / total_rows


def initial_window_estimate(target_selectivity, total_rows=None):
    """Titik awal pencarian boundary sebelum COUNT(*) dijalankan.

    Berbasis asumsi arrival rate seragam sepanjang periode observasi MMDEC
    (92 hari). Trafik AIS nyata tidak seragam, jadi hasilnya wajib dikoreksi
    dengan COUNT(*) aktual.
    """
    minutes = uniform_window_minutes(target_selectivity)
    rows = (
        expected_matched_rows(target_selectivity, total_rows)
        if total_rows
        else expected_matched_rows(target_selectivity)
    )
    return {
        "target_selectivity": target_selectivity,
        "window_minutes": minutes,
        "window_hours": minutes / 60,
        "window_days": minutes / 1440,
        "expected_matched_rows": rows,
    }


def audit_bands(bands, tolerance=DEFAULT_BAND_TOLERANCE):
    """Gate G5: semua band harus berada dalam toleransi dan terurut naik."""
    rows = [
        {
            "target": b.target,
            "measured": b.measured,
            "relative_error": b.relative_error,
            "accepted": b.accepted(tolerance),
        }
        for b in bands
    ]
    measured = [r["measured"] for r in rows]
    return {
        "bands": rows,
        "all_accepted": all(r["accepted"] for r in rows),
        "monotonic": measured == sorted(measured),
    }
