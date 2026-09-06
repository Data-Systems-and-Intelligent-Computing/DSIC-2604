import pytest

from src.inspect_parquet import (
    file_size_separation,
    grid_is_feasible,
    projected_file_count,
    row_group_control,
)


def _variant(median, p25, p75, minimum, maximum, file_count, rg_median):
    return {
        "file_count": file_count,
        "file_size_mib_median": median,
        "file_size_mib_p25": p25,
        "file_size_mib_p75": p75,
        "file_size_mib_min": minimum,
        "file_size_mib_max": maximum,
        "row_group_mib_median": rg_median,
    }


def test_primary_grid_is_strictly_increasing():
    grid = [32, 64, 128, 256]
    assert grid == sorted(set(grid))


def test_well_separated_variants_pass_g3():
    small = _variant(31.0, 30.0, 32.0, 28.0, 33.0, 27, 31.0)
    large = _variant(126.0, 124.0, 128.0, 120.0, 130.0, 7, 31.5)
    sep = file_size_separation(small, large)
    assert sep["separated"]
    assert not sep["iqr_overlap"]
    assert sep["median_ratio"] == pytest.approx(126.0 / 31.0)


def test_overlapping_variants_fail_g3():
    small = _variant(60.0, 40.0, 90.0, 20.0, 130.0, 14, 31.0)
    large = _variant(80.0, 55.0, 120.0, 25.0, 140.0, 10, 31.0)
    assert not file_size_separation(small, large)["separated"]


def test_row_group_must_stay_fixed_across_variants():
    controlled = {
        "32": _variant(31.0, 30.0, 32.0, 28.0, 33.0, 27, 31.0),
        "256": _variant(250.0, 245.0, 255.0, 240.0, 260.0, 4, 32.0),
    }
    assert row_group_control(controlled)["controlled"]

    # Row-group ikut berskala bersama file size: confound yang dilarang.
    confounded = {
        "32": _variant(31.0, 30.0, 32.0, 28.0, 33.0, 27, 8.0),
        "256": _variant(250.0, 245.0, 255.0, 240.0, 260.0, 4, 64.0),
    }
    assert not row_group_control(confounded)["controlled"]


def test_largest_condition_needs_enough_files():
    assert grid_is_feasible({"file_count": 16})["preferred_met"]
    assert grid_is_feasible({"file_count": 8})["feasible"]
    assert not grid_is_feasible({"file_count": 4})["feasible"]


def test_projected_file_count_drives_grid_choice():
    # Tabel ~900 MiB: 256 MiB hanya menghasilkan 3 file -> grid utama tidak layak.
    assert projected_file_count(900, 256) == 3
    assert not grid_is_feasible({"file_count": projected_file_count(900, 256)})["feasible"]
    # Fallback grid 8/16/32/64 MiB tetap layak pada ukuran tabel yang sama.
    assert grid_is_feasible({"file_count": projected_file_count(900, 64)})["feasible"]
