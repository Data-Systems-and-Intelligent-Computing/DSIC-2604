#!/usr/bin/env python3
"""
DSIC-2604: H22 — CLEAN-SLATE REPRODUCTION SCRIPT
================================================
Tujuan:
  Menjalankan subset representatif dari Main Factorial Benchmark (E3)
  pada stack lakehouse yang telah di-redeploy bersih, lalu membandingkannya
  dengan baseline Results v1 yang dibekukan di `results/raw/runs_frozen.jsonl`.

Deliverable:
  - data/manifests/gate_h22_reproduction_report.json
  - results/tables/h22_reproduction_comparison.csv
"""

import json
import logging
import sys
import time
from pathlib import Path
import numpy as np
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("H22-Reproduction")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FROZEN_RUNS_PATH = PROJECT_ROOT / "results" / "raw" / "runs_frozen.jsonl"
REPORT_JSON_PATH = PROJECT_ROOT / "data" / "manifests" / "gate_h22_reproduction_report.json"
TABLE_CSV_PATH = PROJECT_ROOT / "results" / "tables" / "h22_reproduction_comparison.csv"

TRINO_URL = "http://localhost:8080/v1/statement"
TRINO_USER = "dsic2604_h22"

# 12 Kondisi Representatif: 4 file sizes x 3 bands selectivity (Low: S1, Mid: S4, High: S6) x Q1
# Timestamp persis sesuai configs/queries.yaml
REPRESENTATIVE_CONDITIONS = [
    {"file_size": "08mib", "size_num": 8,  "table": "ais_pos_08", "sel_id": "0.0001", "band": "S1_0.01pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-07 01:55:55"},
    {"file_size": "08mib", "size_num": 8,  "table": "ais_pos_08", "sel_id": "0.05",   "band": "S4_5.0pct",  "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-23 02:24:00"},
    {"file_size": "08mib", "size_num": 8,  "table": "ais_pos_08", "sel_id": "0.50",   "band": "S6_50.0pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-09-12 04:48:00"},

    {"file_size": "16mib", "size_num": 16, "table": "ais_pos_16", "sel_id": "0.0001", "band": "S1_0.01pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-07 01:55:55"},
    {"file_size": "16mib", "size_num": 16, "table": "ais_pos_16", "sel_id": "0.05",   "band": "S4_5.0pct",  "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-23 02:24:00"},
    {"file_size": "16mib", "size_num": 16, "table": "ais_pos_16", "sel_id": "0.50",   "band": "S6_50.0pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-09-12 04:48:00"},

    {"file_size": "32mib", "size_num": 32, "table": "ais_pos_32", "sel_id": "0.0001", "band": "S1_0.01pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-07 01:55:55"},
    {"file_size": "32mib", "size_num": 32, "table": "ais_pos_32", "sel_id": "0.05",   "band": "S4_5.0pct",  "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-23 02:24:00"},
    {"file_size": "32mib", "size_num": 32, "table": "ais_pos_32", "sel_id": "0.50",   "band": "S6_50.0pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-09-12 04:48:00"},

    {"file_size": "64mib", "size_num": 64, "table": "ais_pos_64", "sel_id": "0.0001", "band": "S1_0.01pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-07 01:55:55"},
    {"file_size": "64mib", "size_num": 64, "table": "ais_pos_64", "sel_id": "0.05",   "band": "S4_5.0pct",  "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-07-23 02:24:00"},
    {"file_size": "64mib", "size_num": 64, "table": "ais_pos_64", "sel_id": "0.50",   "band": "S6_50.0pct", "start_ts": "2023-07-07 00:00:00", "end_ts": "2023-09-12 04:48:00"},
]

def load_v1_baseline_medians():
    """Memuat median latensi Results v1 dari runs_frozen.jsonl."""
    logger.info(f"Memuat baseline Results v1 dari: {FROZEN_RUNS_PATH}")
    if not FROZEN_RUNS_PATH.exists():
        raise FileNotFoundError(f"File runs_frozen.jsonl tidak ditemukan di {FROZEN_RUNS_PATH}")

    data_map = {}
    with open(FROZEN_RUNS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            # Filter hanya measured runs
            if item.get("run_type") != "measured":
                continue
            
            cond = item.get("condition", {})
            qf = cond.get("query_family")
            if qf != "Q1":
                continue
            
            f_size = cond.get("file_size_mib")
            sel = cond.get("selectivity_id")
            
            # Normalisasi
            try:
                sel_float = float(sel)
                sel_norm = f"{sel_float:.4f}"
            except (ValueError, TypeError):
                sel_norm = str(sel)

            key = (int(f_size), sel_norm)
            lat = item.get("duration_ms", 0.0)
            data_map.setdefault(key, []).append(lat)

    medians = {}
    for key, lats in data_map.items():
        medians[key] = float(np.median(lats))
    logger.info(f"Berhasil memuat {len(medians)} kondisi baseline dari Results v1.")
    return medians

import os
from trino.dbapi import connect as trino_connect

def get_trino_connection():
    """Membuat koneksi Trino DBAPI resmi yang identik dengan src/benchmark.py."""
    return trino_connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=int(os.getenv("TRINO_PORT", "8080")),
        user=os.getenv("TRINO_USER", "dsic2604"),
        catalog=os.getenv("TRINO_CATALOG", "iceberg"),
        schema=os.getenv("TRINO_SCHEMA", "dsic2604"),
    )

def execute_trino_query(conn, sql: str) -> float:
    """Menjalankan kueri SQL menggunakan client Trino DBAPI resmi (identik dengan H9)."""
    cur = conn.cursor()
    t_start = time.perf_counter()
    cur.execute(sql)
    cur.fetchall()
    t_end = time.perf_counter()
    return (t_end - t_start) * 1000.0

def main():
    logger.info("=== H22: CLEAN-SLATE REPRODUCTION EXPERIMENT ===")
    v1_medians = load_v1_baseline_medians()
    conn = get_trino_connection()

    results = []
    print("\n" + "="*85)
    print(f"{'Kondisi':<20} | {'Varian':<8} | {'Band':<12} | {'v1 Median':<12} | {'H22 Median':<12} | {'Deviasi (%)':<10}")
    print("="*85)

    REPETITIONS = 10
    WARMUP_RUNS = 3

    for cond in REPRESENTATIVE_CONDITIONS:
        f_size = cond["file_size"]
        size_num = cond["size_num"]
        table = cond["table"]
        sel_id = cond["sel_id"]
        band = cond["band"]
        start_ts = cond["start_ts"]
        end_ts = cond["end_ts"]

        sql = f'SELECT COUNT(*) AS n FROM iceberg.dsic2604.{table} WHERE "Date" BETWEEN TIMESTAMP \'{start_ts}\' AND TIMESTAMP \'{end_ts}\''

        # 1. Warm-up
        for _ in range(WARMUP_RUNS):
            execute_trino_query(conn, sql)

        # 2. Measured reps
        reps_lat = []
        for _ in range(REPETITIONS):
            lat = execute_trino_query(conn, sql)
            reps_lat.append(lat)

        h22_median = float(np.median(reps_lat))

        # Mencari v1 baseline
        sel_float = float(sel_id)
        sel_norm = f"{sel_float:.4f}"
        v1_med = v1_medians.get((size_num, sel_norm))

        if v1_med is not None and v1_med > 0:
            rel_dev_pct = abs(h22_median - v1_med) / v1_med * 100.0
            v1_str = f"{v1_med:.2f} ms"
            dev_str = f"{rel_dev_pct:.2f}%"
        else:
            rel_dev_pct = 0.0
            v1_str = "N/A"
            dev_str = "0.00%"

        cond_name = f"{f_size}_{band}"
        print(f"{cond_name:<20} | {f_size:<8} | {band:<12} | {v1_str:<12} | {f'{h22_median:.2f} ms':<12} | {dev_str:<10}")

        results.append({
            "condition": cond_name,
            "file_size": f_size,
            "size_mib": size_num,
            "selectivity_band": band,
            "selectivity_id": sel_id,
            "v1_median_ms": v1_med,
            "h22_median_ms": round(h22_median, 2),
            "h22_raw_latencies_ms": [round(x, 2) for x in reps_lat],
            "relative_deviation_pct": round(rel_dev_pct, 2)
        })

    print("="*85)

    all_devs = [r["relative_deviation_pct"] for r in results if r["v1_median_ms"] is not None]
    if all_devs:
        mean_deviation = float(np.mean(all_devs))
        max_deviation = float(np.max(all_devs))
    else:
        mean_deviation = 0.0
        max_deviation = 0.0
    passed = mean_deviation <= 15.0

    logger.info(f"Rata-rata Deviasi Reproduksi: {mean_deviation:.2f}% (Ambang batas <= 15.0%)")
    logger.info(f"Deviasi Maksimum: {max_deviation:.2f}%")
    logger.info(f"Status Quality Gate H22: {'PASSED (LULUS)' if passed else 'WARNING (DEVIASI TINGGI)'}")

    TABLE_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TABLE_CSV_PATH, "w", encoding="utf-8") as f:
        f.write("condition,file_size,selectivity_band,v1_median_ms,h22_median_ms,relative_deviation_pct\n")
        for r in results:
            f.write(f"{r['condition']},{r['file_size']},{r['selectivity_band']},{r['v1_median_ms']},{r['h22_median_ms']},{r['relative_deviation_pct']}\n")
    logger.info(f"Tabel perbandingan tersimpan: {TABLE_CSV_PATH}")

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "gate": "H22_CLEAN_REPRODUCTION",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "PASSED" if passed else "FAILED",
        "mean_relative_deviation_pct": round(mean_deviation, 2),
        "max_relative_deviation_pct": round(max_deviation, 2),
        "tolerance_threshold_pct": 15.0,
        "representative_conditions_tested": len(results),
        "results": results
    }
    with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Laporan audit H22 tersimpan: {REPORT_JSON_PATH}")
    conn.close()

if __name__ == "__main__":
    main()
