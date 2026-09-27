"""Block-randomized repeated-query benchmark harness for DSIC-2604.

Mengeksekusi factorial grid (file_size × selectivity × query_family) dengan:
- Block-randomized run order (seed-controlled)
- Warm-up runs per condition (tidak direkam ke measured)
- Trino telemetry collection via REST API (Gate G6)
- Per-run JSONL logging ke results/raw/runs.jsonl
"""
import os
import sys
import time
import json
import random
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from trino.dbapi import connect as trino_connect
from src.common import get_project_root, load_yaml, write_jsonl
from src.collect_trino_stats import normalize_query_info

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunCondition:
    """Satu kondisi eksperimental dalam factorial grid."""
    file_size_mib: int
    query_family: str
    selectivity_id: str


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_trino_connection():
    """Create a Trino DBAPI connection from environment variables."""
    return trino_connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=int(os.getenv("TRINO_PORT", "8080")),
        user=os.getenv("TRINO_USER", "dsic2604"),
        catalog=os.getenv("TRINO_CATALOG", "iceberg"),
        schema=os.getenv("TRINO_SCHEMA", "dsic2604"),
    )


def _trino_rest_base():
    """Base URL for Trino REST API."""
    host = os.getenv("TRINO_HOST", "localhost")
    port = os.getenv("TRINO_PORT", "8080")
    return f"http://{host}:{port}"


def fetch_query_info(query_id):
    """Fetch QueryInfo from Trino REST API for telemetry.

    Trino menyediakan /v1/query/{queryId} yang mengembalikan detail lengkap
    termasuk queryStats (physical input, splits, CPU, memory).
    """
    url = f"{_trino_rest_base()}/v1/query/{query_id}"
    try:
        resp = requests.get(
            url,
            headers={"X-Trino-User": os.getenv("TRINO_USER", "dsic2604")},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch query info for {query_id}: {e}")
    return None


# ---------------------------------------------------------------------------
# Query execution with telemetry
# ---------------------------------------------------------------------------

def execute_query_with_telemetry(conn, sql):
    """Execute query and collect both latency and Trino telemetry.

    Returns:
        tuple: (duration_ms, row_count, query_id, telemetry_dict)
    """
    cur = conn.cursor()

    start_time = time.perf_counter()
    cur.execute(sql)
    rows = cur.fetchall()
    end_time = time.perf_counter()

    duration_ms = (end_time - start_time) * 1000.0
    row_count = len(rows)

    # Extract query_id from cursor — trino-python-client exposes this
    query_id = getattr(cur, "query_id", None) or getattr(
        getattr(cur, "_query", None), "query_id", None
    )

    telemetry = {}
    if query_id:
        info = fetch_query_info(query_id)
        if info:
            telemetry = normalize_query_info(info)

    return duration_ms, row_count, query_id, telemetry


def execute_query(conn, sql):
    """Backward-compatible simple execution (latency only)."""
    dur_ms, row_count, _, _ = execute_query_with_telemetry(conn, sql)
    return dur_ms, row_count


# ---------------------------------------------------------------------------
# Randomization
# ---------------------------------------------------------------------------

def randomized_block(conditions, seed):
    """Shuffle conditions in a single block, deterministically."""
    items = list(conditions)
    random.Random(seed).shuffle(items)
    return items


def generate_run_order(conditions, repetitions, warmup_per_condition, seed):
    """Generate block-randomized run order.

    Each block contains all conditions in random order. The first
    `warmup_per_condition` blocks are warm-up (not measured).

    Args:
        conditions: List of RunCondition.
        repetitions: Number of measured repetitions.
        warmup_per_condition: Number of warm-up blocks.
        seed: Random seed for reproducibility.

    Returns:
        List of (block_idx, is_warmup, RunCondition) tuples.
    """
    total_blocks = warmup_per_condition + repetitions
    runs = []
    rng = random.Random(seed)

    for block_idx in range(total_blocks):
        is_warmup = block_idx < warmup_per_condition
        block_seed = rng.randint(0, 2**31)
        shuffled = randomized_block(conditions, block_seed)
        for cond in shuffled:
            runs.append((block_idx, is_warmup, cond))

    return runs


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_benchmark_config():
    """Load benchmark.yaml, queries.yaml, and selectivity bands."""
    root = get_project_root()
    bench_cfg = load_yaml(root / "configs" / "benchmark.yaml")
    queries_cfg = load_yaml(root / "configs" / "queries.yaml")

    return bench_cfg, queries_cfg


def _normalize_selectivity_id(band, available_keys):
    """Resolve float band ke string key yang ada di queries.yaml.

    Masalah: str(0.5) = '0.5', tapi queries.yaml memakai key '0.50'.
    Strategi: coba str(band) dulu, lalu coba float-comparison ke semua key.
    """
    s = str(band)
    if s in available_keys:
        return s
    # fallback: bandingkan nilai numerik
    try:
        band_f = float(band)
        for k in available_keys:
            try:
                if abs(float(k) - band_f) < 1e-9:
                    return k
            except ValueError:
                pass
    except (TypeError, ValueError):
        pass
    return s  # biarkan KeyError terjadi saat runtime dengan pesan jelas


def build_conditions(bench_cfg, available_band_keys=None):
    """Build all RunCondition from the factorial grid."""
    factors = bench_cfg["factors"]
    conditions = []
    for fs in factors["file_size_mib"]:
        for band in factors["selectivity_bands"]:
            for qf in factors["query_families"]:
                sel_id = (
                    _normalize_selectivity_id(band, available_band_keys)
                    if available_band_keys
                    else str(band)
                )
                conditions.append(RunCondition(
                    file_size_mib=fs,
                    query_family=qf,
                    selectivity_id=sel_id,
                ))
    return conditions


def build_sql(queries_cfg, condition):
    """Build SQL string for a given RunCondition."""
    query_template = queries_cfg["queries"][condition.query_family]["template"]
    band_info = queries_cfg["selectivity_bands"][condition.selectivity_id]

    table_name = (
        f"iceberg.dsic2604.ais_pos_{condition.file_size_mib:02d}"
    )

    sql = query_template.format(
        table_name=table_name,
        start_ts=band_info["start_ts"],
        end_ts=band_info["end_ts"],
    )
    return sql.strip()


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def record_run(path, payload):
    """Append a run record as JSONL."""
    write_jsonl(path, payload)


# ---------------------------------------------------------------------------
# Main benchmark harness
# ---------------------------------------------------------------------------

def run_benchmark(dry_run=False, max_runs=None):
    """Execute the full factorial benchmark.

    Args:
        dry_run: If True, run only 1 block (no warm-up) for observability check.
        max_runs: Optional cap on total runs (for testing).

    Returns:
        dict: Summary report.
    """
    root = get_project_root()
    bench_cfg, queries_cfg = load_benchmark_config()

    benchmark = bench_cfg["benchmark"]
    seed = benchmark["seed"]
    warmup_per_condition = benchmark["warmup_runs_per_condition"]
    measured_reps = benchmark["measured_repetitions_per_condition"]
    raw_log_path = root / benchmark["raw_log_path"]

    if dry_run:
        warmup_per_condition = 0
        measured_reps = 1
        logger.info("=== DRY-RUN MODE (1 block, no warm-up) ===")

    # Resolusi selectivity_id ke key yang ada di queries.yaml
    available_band_keys = list(queries_cfg.get("selectivity_bands", {}).keys())
    conditions = build_conditions(bench_cfg, available_band_keys=available_band_keys)
    logger.info(f"Factorial grid: {len(conditions)} conditions")
    logger.info(f"  File sizes: {bench_cfg['factors']['file_size_mib']}")
    logger.info(f"  Selectivity bands: {bench_cfg['factors']['selectivity_bands']}")
    logger.info(f"  Query families: {bench_cfg['factors']['query_families']}")
    logger.info(f"  Warm-up blocks: {warmup_per_condition}")
    logger.info(f"  Measured reps: {measured_reps}")

    run_order = generate_run_order(
        conditions, measured_reps, warmup_per_condition, seed
    )

    if max_runs:
        run_order = run_order[:max_runs]

    total_runs = len(run_order)
    warmup_count = sum(1 for _, w, _ in run_order if w)
    measured_count = total_runs - warmup_count
    logger.info(f"Total runs: {total_runs} ({warmup_count} warm-up + {measured_count} measured)")

    # Ensure output directory exists
    raw_log_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_trino_connection()

    run_start = datetime.now(timezone.utc)
    completed = 0
    failed = 0
    missing_telemetry_runs = 0

    try:
        for run_idx, (block_idx, is_warmup, cond) in enumerate(run_order):
            sql = build_sql(queries_cfg, cond)
            run_type = "warmup" if is_warmup else "measured"

            try:
                duration_ms, row_count, query_id, telemetry = (
                    execute_query_with_telemetry(conn, sql)
                )
                status = "FINISHED"

                if telemetry.get("missing_metrics"):
                    missing_telemetry_runs += 1

            except Exception as e:
                duration_ms = None
                row_count = None
                query_id = None
                telemetry = {}
                status = "FAILED"
                failed += 1
                logger.error(
                    f"Run {run_idx + 1}/{total_runs} FAILED: "
                    f"{cond.query_family} sel={cond.selectivity_id} "
                    f"fs={cond.file_size_mib}: {e}"
                )

            payload = {
                "run_index": run_idx,
                "block_index": block_idx,
                "run_type": run_type,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "condition": asdict(cond),
                "sql": sql,
                "duration_ms": duration_ms,
                "row_count": row_count,
                "query_id": query_id,
                **telemetry,
            }

            # Record all runs (including warm-up and failed) per benchmark.yaml
            record_run(raw_log_path, payload)
            completed += 1

            if completed % 50 == 0 or completed == total_runs:
                elapsed = time.perf_counter()
                logger.info(
                    f"Progress: {completed}/{total_runs} "
                    f"({run_type}, block={block_idx}, "
                    f"{cond.query_family} sel={cond.selectivity_id} "
                    f"fs={cond.file_size_mib} MiB "
                    f"→ {duration_ms:.1f} ms)" if duration_ms else
                    f"Progress: {completed}/{total_runs} (FAILED)"
                )

    finally:
        conn.close()

    run_end = datetime.now(timezone.utc)

    report = {
        "benchmark_start": run_start.isoformat(),
        "benchmark_end": run_end.isoformat(),
        "wall_time_seconds": (run_end - run_start).total_seconds(),
        "total_runs": total_runs,
        "warmup_runs": warmup_count,
        "measured_runs": measured_count,
        "completed": completed,
        "failed": failed,
        "missing_telemetry_runs": missing_telemetry_runs,
        "conditions": len(conditions),
        "seed": seed,
        "dry_run": dry_run,
        "raw_log_path": str(raw_log_path),
    }

    return report
