"""Semantic equivalence checks across layout variants.

Verifies that all Iceberg table variants produce identical query results
for Q1 (predicate scan), Q2 (selective aggregate), and Q3 (group by).
This is a critical integrity check: different file layouts must not change
query semantics.
"""
import os
import logging
from trino.dbapi import connect as trino_connect

logger = logging.getLogger(__name__)


def get_trino_connection():
    """Create a Trino DBAPI connection from environment variables."""
    return trino_connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=int(os.getenv("TRINO_PORT", "8080")),
        user=os.getenv("TRINO_USER", "dsic2604"),
        catalog=os.getenv("TRINO_CATALOG", "iceberg"),
        schema=os.getenv("TRINO_SCHEMA", "dsic2604"),
    )


def run_query(conn, sql):
    """Execute a SQL query and return all rows."""
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in rows]


def run_count(conn, table_name):
    """Get total row count for a table."""
    result = run_query(conn, f"SELECT COUNT(*) AS n FROM {table_name}")
    return result[0]["n"]


def run_q1(conn, table_name, start_ts, end_ts):
    """Q1: Predicate scan count."""
    sql = (
        f"SELECT COUNT(*) AS n FROM {table_name} "
        f"WHERE \"Date\" BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}'"
    )
    return run_query(conn, sql)[0]["n"]


def run_q2(conn, table_name, start_ts, end_ts):
    """Q2: Selective aggregate (AVG, MAX of SpeedOverGround)."""
    sql = (
        f"SELECT CAST(AVG(\"SpeedOverGround\") AS DOUBLE) AS avg_sog, "
        f"CAST(MAX(\"SpeedOverGround\") AS DOUBLE) AS max_sog "
        f"FROM {table_name} "
        f"WHERE \"Date\" BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}'"
    )
    return run_query(conn, sql)[0]


def run_q3(conn, table_name, start_ts, end_ts):
    """Q3: Selective group by MessageType."""
    sql = (
        f"SELECT \"MessageType\", COUNT(*) AS n, "
        f"CAST(AVG(\"SpeedOverGround\") AS DOUBLE) AS avg_sog "
        f"FROM {table_name} "
        f"WHERE \"Date\" BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}' "
        f"GROUP BY \"MessageType\" ORDER BY \"MessageType\""
    )
    return run_query(conn, sql)


def assert_same_scalar_results(results_by_variant):
    """Assert all variants produce identical scalar results."""
    values = list(results_by_variant.values())
    if not values:
        raise ValueError("No results supplied")
    first = values[0]
    for k, v in results_by_variant.items():
        if v != first:
            raise AssertionError(f"Semantic mismatch for {k}: {v} != {first}")


def assert_row_count_equal(counts_by_variant, expected_count=None):
    """Assert all variants have the same row count (and optionally match expected)."""
    counts = list(counts_by_variant.values())
    if not counts:
        raise ValueError("No counts supplied")
    first = counts[0]
    for k, c in counts_by_variant.items():
        if c != first:
            raise AssertionError(
                f"Row count mismatch for {k}: {c} != {first}"
            )
    if expected_count is not None and first != expected_count:
        raise AssertionError(
            f"Row count {first} != expected {expected_count}"
        )


def run_equivalence_queries(table_names, start_ts, end_ts, expected_total_rows=None):
    """Run Q1, Q2, Q3 against all variants and check equivalence.

    Args:
        table_names: dict mapping variant label -> full Iceberg table name
        start_ts: Start timestamp for predicates (e.g. '2023-07-15 00:00:00')
        end_ts: End timestamp for predicates (e.g. '2023-07-16 00:00:00')
        expected_total_rows: If set, verify total row count matches

    Returns:
        dict with test results for each query family
    """
    conn = get_trino_connection()
    results = {}

    try:
        # Row count check
        counts = {}
        for label, tbl in table_names.items():
            counts[label] = run_count(conn, tbl)
        assert_row_count_equal(counts, expected_total_rows)
        results["row_count"] = {"status": "PASSED", "counts": counts}

        # Q1: predicate scan
        q1_results = {}
        for label, tbl in table_names.items():
            q1_results[label] = run_q1(conn, tbl, start_ts, end_ts)
        assert_same_scalar_results(q1_results)
        results["Q1"] = {"status": "PASSED", "results": q1_results}

        # Q2: selective aggregate
        q2_results = {}
        for label, tbl in table_names.items():
            q2_results[label] = run_q2(conn, tbl, start_ts, end_ts)
        # Compare with tolerance for floating point
        q2_values = list(q2_results.values())
        q2_first = q2_values[0]
        for label, v in q2_results.items():
            for key in ("avg_sog", "max_sog"):
                if v[key] is not None and q2_first[key] is not None:
                    if abs(v[key] - q2_first[key]) > 1e-6:
                        raise AssertionError(
                            f"Q2 {key} mismatch for {label}: {v[key]} vs {q2_first[key]}"
                        )
        results["Q2"] = {"status": "PASSED", "results": q2_results}

        # Q3: selective group by
        q3_results = {}
        for label, tbl in table_names.items():
            q3_results[label] = run_q3(conn, tbl, start_ts, end_ts)
        # Compare row-by-row with tolerance
        q3_first = q3_results[list(q3_results.keys())[0]]
        for label, rows in q3_results.items():
            if len(rows) != len(q3_first):
                raise AssertionError(
                    f"Q3 group count mismatch for {label}: {len(rows)} vs {len(q3_first)}"
                )
            for i, (r, f) in enumerate(zip(rows, q3_first)):
                if r["MessageType"] != f["MessageType"] or r["n"] != f["n"]:
                    raise AssertionError(
                        f"Q3 row {i} mismatch for {label}: {r} vs {f}"
                    )
        results["Q3"] = {"status": "PASSED", "results": {
            k: [{"MessageType": r["MessageType"], "n": r["n"]} for r in v]
            for k, v in q3_results.items()
        }}

    except AssertionError as e:
        logger.error(f"Equivalence check failed: {e}")
        raise
    finally:
        conn.close()

    return results
