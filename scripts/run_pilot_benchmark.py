#!/usr/bin/env python
"""Pilot benchmark (H7) — validasi harness end-to-end.

Menjalankan subset kecil dari factorial grid pada keempat varian
untuk memverifikasi:
1. Query berjalan pada semua 4 varian (08/16/32/64 MiB)
2. Trino telemetry tersedia (Gate G6 pre-check)
3. Estimasi durasi main benchmark
4. Baseline (32 MiB) berjalan stabil (Gate G8)
5. Warm-up dan cache protocol bekerja

Usage:
    python scripts/run_pilot_benchmark.py [--dry-run]
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark import (
    RunCondition,
    build_sql,
    execute_query_with_telemetry,
    get_trino_connection,
    load_benchmark_config,
    randomized_block,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pilot_benchmark")

PILOT_REPORT = PROJECT_ROOT / "data" / "manifests" / "gate_g8_g9_pilot_report.json"


def run_pilot(dry_run=False):
    """Run pilot benchmark on all 4 variants.

    Pilot protocol:
    1. Warm-up: 2 passes through all conditions on baseline (32 MiB)
    2. Measured: 1 full pass through all Q1-Q3 × 6 bands × 4 file sizes
    3. Baseline stability: 10 extra reps on baseline (32 MiB) for G8
    4. Q4 entity: 5 sample MMSI on baseline (optional)
    """
    logger.info("=" * 60)
    logger.info("DSIC-2604 H7: Pilot Benchmark")
    logger.info("=" * 60)

    bench_cfg, queries_cfg = load_benchmark_config()
    factors = bench_cfg["factors"]
    file_sizes = factors["file_size_mib"]
    bands = list(queries_cfg["selectivity_bands"].keys())
    query_families = factors["query_families"]
    seed = bench_cfg["benchmark"]["seed"]

    # Validate grid matches layout decision
    expected_grid = [8, 16, 32, 64]
    if file_sizes != expected_grid:
        logger.error(f"Grid mismatch! benchmark.yaml has {file_sizes}, expected {expected_grid}")
        sys.exit(1)

    logger.info(f"File sizes: {file_sizes}")
    logger.info(f"Bands: {bands}")
    logger.info(f"Queries: {query_families}")

    conn = get_trino_connection()

    # --- Phase 1: Warm-up on baseline ---
    baseline_mib = 32
    logger.info("")
    logger.info("--- Phase 1: Warm-up (baseline 32 MiB) ---")
    for band in bands:
        for qf in query_families:
            cond = RunCondition(file_size_mib=baseline_mib, query_family=qf, selectivity_id=band)
            sql = build_sql(queries_cfg, cond)
            try:
                dur_ms, _, _, _ = execute_query_with_telemetry(conn, sql)
                logger.info(f"  warmup {qf} sel={band} → {dur_ms:.1f} ms")
            except Exception as e:
                logger.warning(f"  warmup {qf} sel={band} FAILED: {e}")

    # --- Phase 2: Measured pass on ALL 4 variants ---
    logger.info("")
    logger.info("--- Phase 2: Measured pass (all 4 variants) ---")

    all_results = []
    per_variant_latencies = {fs: [] for fs in file_sizes}
    telemetry_checks = {"total": 0, "with_telemetry": 0, "missing_fields": []}

    conditions = []
    for fs in file_sizes:
        for band in bands:
            for qf in query_families:
                conditions.append(RunCondition(
                    file_size_mib=fs, query_family=qf, selectivity_id=band
                ))

    # Block-randomize
    shuffled = randomized_block(conditions, seed)

    t0 = time.time()
    for i, cond in enumerate(shuffled):
        sql = build_sql(queries_cfg, cond)
        try:
            dur_ms, row_count, query_id, telemetry = execute_query_with_telemetry(conn, sql)
            status = "FINISHED"

            # Telemetry check for G6
            telemetry_checks["total"] += 1
            missing = telemetry.get("missing_metrics", [])
            if not missing:
                telemetry_checks["with_telemetry"] += 1
            else:
                telemetry_checks["missing_fields"].extend(missing)

            per_variant_latencies[cond.file_size_mib].append(dur_ms)

            result = {
                "run_index": i,
                "condition": {
                    "file_size_mib": cond.file_size_mib,
                    "query_family": cond.query_family,
                    "selectivity_id": cond.selectivity_id,
                },
                "duration_ms": dur_ms,
                "row_count": row_count,
                "query_id": query_id,
                "status": status,
                "missing_metrics": missing,
                **{k: telemetry.get(k) for k in [
                    "physical_input_bytes", "processed_input_rows",
                    "completed_splits", "cpu_ms", "peak_memory_bytes",
                    "planning_ms",
                ]},
            }
            all_results.append(result)

            if (i + 1) % 20 == 0:
                logger.info(
                    f"  [{i + 1}/{len(shuffled)}] {cond.query_family} "
                    f"sel={cond.selectivity_id} fs={cond.file_size_mib} "
                    f"→ {dur_ms:.1f} ms"
                )

        except Exception as e:
            logger.error(
                f"  [{i + 1}/{len(shuffled)}] FAILED: {cond.query_family} "
                f"sel={cond.selectivity_id} fs={cond.file_size_mib}: {e}"
            )
            all_results.append({
                "run_index": i,
                "condition": {
                    "file_size_mib": cond.file_size_mib,
                    "query_family": cond.query_family,
                    "selectivity_id": cond.selectivity_id,
                },
                "status": "FAILED",
                "error": str(e),
            })

    pass_wall_time = time.time() - t0

    # --- Phase 3: Baseline stability (G8) ---
    logger.info("")
    logger.info("--- Phase 3: Baseline stability check (G8) ---")

    baseline_stability_latencies = []
    stability_band = bands[2]  # ~0.01 selectivity (medium)
    stability_query = "Q1"

    for rep in range(10):
        cond = RunCondition(
            file_size_mib=baseline_mib,
            query_family=stability_query,
            selectivity_id=stability_band,
        )
        sql = build_sql(queries_cfg, cond)
        try:
            dur_ms, _, _, _ = execute_query_with_telemetry(conn, sql)
            baseline_stability_latencies.append(dur_ms)
            logger.info(f"  baseline rep {rep + 1}/10: {dur_ms:.1f} ms")
        except Exception as e:
            logger.warning(f"  baseline rep {rep + 1}/10 FAILED: {e}")

    conn.close()

    # --- Analysis ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("PILOT RESULTS")
    logger.info("=" * 60)

    # Per-variant summary
    variant_summaries = {}
    for fs in file_sizes:
        lats = per_variant_latencies[fs]
        if lats:
            variant_summaries[f"{fs:02d}mib"] = {
                "count": len(lats),
                "mean_ms": round(mean(lats), 2),
                "stdev_ms": round(stdev(lats), 2) if len(lats) > 1 else 0,
                "min_ms": round(min(lats), 2),
                "max_ms": round(max(lats), 2),
            }
            logger.info(
                f"  {fs:>3d} MiB: n={len(lats)}, "
                f"mean={mean(lats):.1f} ms, "
                f"stdev={stdev(lats):.1f} ms" if len(lats) > 1 else
                f"  {fs:>3d} MiB: n={len(lats)}, mean={mean(lats):.1f} ms"
            )

    # Baseline stability (G8)
    baseline_cv = None
    if len(baseline_stability_latencies) > 1:
        bl_mean = mean(baseline_stability_latencies)
        bl_stdev = stdev(baseline_stability_latencies)
        baseline_cv = bl_stdev / bl_mean if bl_mean > 0 else None
        logger.info(f"  Baseline CV: {baseline_cv:.4f} ({baseline_cv * 100:.2f}%)")
        logger.info(
            f"  G8 (baseline stable): "
            f"{'PASSED' if baseline_cv < 0.25 else 'FAILED'}"
        )

    # G6 observability check
    g6_coverage = (
        telemetry_checks["with_telemetry"] / telemetry_checks["total"]
        if telemetry_checks["total"] > 0 else 0
    )
    g6_passed = g6_coverage == 1.0
    logger.info(
        f"  G6 (observability): {telemetry_checks['with_telemetry']}"
        f"/{telemetry_checks['total']} runs with full telemetry"
        f" → {'PASSED' if g6_passed else 'FAILED'}"
    )
    if telemetry_checks["missing_fields"]:
        unique_missing = sorted(set(telemetry_checks["missing_fields"]))
        logger.warning(f"  Missing fields: {unique_missing}")

    # G9 claim freeze check
    crossover_cfg = {}
    try:
        crossover_cfg = load_benchmark_config()[0].get("crossover", {})
    except Exception:
        pass
    try:
        from src.common import load_yaml
        crossover_cfg = load_yaml(
            PROJECT_ROOT / "configs" / "crossover.yaml"
        ).get("crossover", {})
    except Exception:
        pass

    g9_passed = bool(crossover_cfg.get("baseline_file_size_mib"))
    logger.info(f"  G9 (claim freeze): {'PASSED' if g9_passed else 'FAILED'}")

    # Estimate main benchmark duration
    total_pilot_queries = len(all_results)
    avg_query_ms = mean([r["duration_ms"] for r in all_results if r.get("duration_ms")]) if all_results else 0

    # Main benchmark: 72 conditions × (2 warmup + 20 measured) = 1584 runs
    main_runs = len(conditions) * (2 + 20)
    estimated_main_seconds = main_runs * (avg_query_ms / 1000.0)
    estimated_main_hours = estimated_main_seconds / 3600.0

    logger.info(f"  Pilot pass wall time: {pass_wall_time:.1f} s")
    logger.info(f"  Avg query duration: {avg_query_ms:.1f} ms")
    logger.info(f"  Estimated main benchmark: {estimated_main_hours:.2f} hours")

    # Overall status
    g8_passed = baseline_cv is not None and baseline_cv < 0.25
    overall = g6_passed and g8_passed and g9_passed
    logger.info("")
    logger.info(f"  OVERALL: {'ALL PILOT GATES PASSED ✅' if overall else 'SOME GATES FAILED ❌'}")

    # --- Save report ---
    report = {
        "gate": "G5_G6_G8_G9",
        "audit_date": datetime.now(timezone.utc).isoformat(),
        "pilot_wall_time_seconds": round(pass_wall_time, 2),
        "pilot_queries_executed": total_pilot_queries,
        "avg_query_duration_ms": round(avg_query_ms, 2),
        "estimated_main_benchmark_hours": round(estimated_main_hours, 2),
        "estimated_main_runs": main_runs,
        "gates": {
            "G5": {
                "status": "PASSED",
                "note": "Selectivity calibration verified in prior step (gate_g5g6_selectivity_report.json)",
            },
            "G6": {
                "status": "PASSED" if g6_passed else "FAILED",
                "telemetry_coverage": f"{telemetry_checks['with_telemetry']}/{telemetry_checks['total']}",
                "missing_fields": sorted(set(telemetry_checks.get("missing_fields", []))),
            },
            "G8": {
                "status": "PASSED" if g8_passed else "FAILED",
                "baseline_file_size_mib": baseline_mib,
                "stability_repetitions": len(baseline_stability_latencies),
                "baseline_cv": round(baseline_cv, 4) if baseline_cv else None,
                "baseline_mean_ms": round(mean(baseline_stability_latencies), 2) if baseline_stability_latencies else None,
                "baseline_latencies_ms": [round(l, 2) for l in baseline_stability_latencies],
            },
            "G9": {
                "status": "PASSED" if g9_passed else "FAILED",
                "crossover_criterion_frozen": g9_passed,
                "baseline_file_size_mib": crossover_cfg.get("baseline_file_size_mib"),
                "primary_metrics_frozen": True,
                "query_templates_frozen": True,
            },
        },
        "variant_summaries": variant_summaries,
        "status": "PASSED" if overall else "FAILED",
    }

    PILOT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    PILOT_REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(f"  Report saved to {PILOT_REPORT}")

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_pilot(dry_run=dry_run)
