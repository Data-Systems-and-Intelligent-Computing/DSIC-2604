"""Semantic equivalence tests across all layout variants (H6).

Verifies that Q1, Q2, Q3 produce identical results on all 4 Iceberg
table variants (ais_pos_08, ais_pos_16, ais_pos_32, ais_pos_64).

Requires:
  - Lakehouse running (MinIO + Iceberg REST + Trino)
  - All 4 variant tables populated by scripts/generate_all_variants.py
"""
import os
import pytest
from src.validate_equivalence import (
    assert_same_scalar_results,
    assert_row_count_equal,
    run_equivalence_queries,
)
from src.generate_layouts import ACTIVE_GRID, table_name
from src.mmdec import AIS_POS_ROWS

# Skip all tests if TRINO_HOST is not reachable
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION", "0") == "1",
    reason="Integration tests skipped (SKIP_INTEGRATION=1)",
)

# Use a mid-range date window for equivalence checks
# (roughly 1 day in August 2023 - ~200k rows at ~0.01 selectivity)
TEST_START_TS = "2023-08-15 00:00:00"
TEST_END_TS = "2023-08-15 23:59:59"


def _variant_tables():
    """Map of variant labels to Iceberg table names."""
    return {f"{m:02d}mib": table_name(m) for m in ACTIVE_GRID}


# ---- Unit tests (no lakehouse needed) ----

def test_assert_same_scalar_basic():
    """Basic unit test for scalar comparison."""
    assert_same_scalar_results({"08mib": 100, "16mib": 100, "32mib": 100, "64mib": 100})


def test_assert_same_scalar_mismatch():
    """Mismatch should raise AssertionError."""
    with pytest.raises(AssertionError):
        assert_same_scalar_results({"08mib": 100, "16mib": 101})


def test_assert_row_count_equal():
    """Row count equality check."""
    assert_row_count_equal({"08mib": 19014229, "16mib": 19014229}, expected_count=19014229)


def test_assert_row_count_mismatch():
    """Row count mismatch should raise."""
    with pytest.raises(AssertionError):
        assert_row_count_equal({"08mib": 19014229, "16mib": 19014228})


# ---- Integration tests (require lakehouse) ----

@pytest.mark.integration
def test_all_variants_have_correct_row_count():
    """Every variant must contain exactly 19,014,229 rows."""
    from src.validate_equivalence import get_trino_connection, run_count

    conn = get_trino_connection()
    try:
        tables = _variant_tables()
        counts = {label: run_count(conn, tbl) for label, tbl in tables.items()}
        assert_row_count_equal(counts, expected_count=AIS_POS_ROWS)
    finally:
        conn.close()


@pytest.mark.integration
def test_q1_q2_q3_equivalence():
    """Q1, Q2, Q3 must produce identical results across all variants."""
    tables = _variant_tables()
    results = run_equivalence_queries(
        tables,
        start_ts=TEST_START_TS,
        end_ts=TEST_END_TS,
        expected_total_rows=AIS_POS_ROWS,
    )
    # All queries should have PASSED status
    for qname, qresult in results.items():
        assert qresult["status"] == "PASSED", f"{qname} failed: {qresult}"
