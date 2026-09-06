import pytest

from src.calibrate_selectivity import (
    SelectivityBand,
    audit_bands,
    initial_window_estimate,
    measured_selectivity,
)
from src.mmdec import AIS_POS_ROWS, OBSERVATION_DAYS


def test_measured_selectivity():
    assert measured_selectivity(100, 1000) == 0.1


def test_measured_selectivity_rejects_impossible_inputs():
    with pytest.raises(ValueError):
        measured_selectivity(10, 0)
    with pytest.raises(ValueError):
        measured_selectivity(1001, 1000)


def test_observation_window_matches_article():
    # 1 Juli - 30 September 2023.
    assert OBSERVATION_DAYS == 92


def test_lowest_band_window_is_operationally_sane():
    est = initial_window_estimate(0.0001)
    # ~13 menit dan ~1.9k baris: cukup kecil untuk menguji skipping,
    # cukup besar untuk tidak menjadi query kosong.
    assert 10 < est["window_minutes"] < 20
    assert est["expected_matched_rows"] > 1000


def test_highest_band_window_fits_observation_period():
    est = initial_window_estimate(0.50)
    assert est["window_days"] < OBSERVATION_DAYS


def test_expected_rows_scale_with_table():
    assert initial_window_estimate(1.0)["expected_matched_rows"] == AIS_POS_ROWS


def test_band_audit_flags_miscalibrated_band():
    total = 1_000_000
    good = [
        SelectivityBand(0.001, "a", "b", 1_000, total),
        SelectivityBand(0.01, "a", "b", 10_400, total),
    ]
    audit = audit_bands(good)
    assert audit["all_accepted"] and audit["monotonic"]

    bad = [SelectivityBand(0.01, "a", "b", 3_000, total)]
    assert not audit_bands(bad)["all_accepted"]
