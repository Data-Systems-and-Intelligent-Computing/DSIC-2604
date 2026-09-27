"""Eksekusi Out-of-Grid Benchmark: Q4 Entity Robustness (H13).

Mengeksekusi kueri Q4 terhadap 50 sampel MMSI yang telah dibekukan
pada 4 varian ukuran file (ais_pos_08, ais_pos_16, ais_pos_32, ais_pos_64).

Total runs = 4 varian x 50 MMSI = 200 eksekusi kueri.

Output Deliverables:
  - results/raw/q4_runs.jsonl
  - data/manifests/q4_robustness_report.json
"""
import os
import sys
import csv
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.benchmark import get_trino_connection, execute_query_with_telemetry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

MMSI_SAMPLE_PATH = Path("data/manifests/q4_mmsi_sample.csv")
OUTPUT_RAW_LOG = Path("results/raw/q4_runs.jsonl")
OUTPUT_REPORT = Path("data/manifests/q4_robustness_report.json")

FILE_SIZES = [8, 16, 32, 64]
TABLES = {
    8: "iceberg.dsic2604.ais_pos_08",
    16: "iceberg.dsic2604.ais_pos_16",
    32: "iceberg.dsic2604.ais_pos_32",
    64: "iceberg.dsic2604.ais_pos_64",
}

def load_mmsi_samples() -> list[int]:
    """Membaca 50 MMSI beku dari data/manifests/q4_mmsi_sample.csv."""
    if not MMSI_SAMPLE_PATH.exists():
        log.error(f"Sampel MMSI tidak ditemukan: {MMSI_SAMPLE_PATH}")
        sys.exit(1)

    mmsis = []
    with open(MMSI_SAMPLE_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mmsis.append(int(row["mmsi"]))
    return mmsis

def run_q4_benchmark():
    log.info("=== H13: BENCHMARK Q4 ENTITY ROBUSTNESS (OUT-OF-GRID) ===")
    
    mmsi_list = load_mmsi_samples()
    log.info(f"Loaded {len(mmsi_list)} sample MMSIs from {MMSI_SAMPLE_PATH}")
    log.info(f"Varian ukuran file: {FILE_SIZES} MiB")
    total_expected = len(FILE_SIZES) * len(mmsi_list)
    log.info(f"Total eksekusi kueri Q4 yang direncanakan: {total_expected} runs")

    conn = get_trino_connection()
    OUTPUT_RAW_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    # Buka raw log untuk append/write
    raw_file = open(OUTPUT_RAW_LOG, "w", encoding="utf-8")

    results_by_variant = {fs: [] for fs in FILE_SIZES}
    all_runs = []
    failed_count = 0
    start_all = time.perf_counter()

    run_idx = 0
    for fs in FILE_SIZES:
        table = TABLES[fs]
        log.info(f"\n--- Menjalankan Q4 pada Varian: {table} ({fs} MiB) ---")
        
        for mmsi in mmsi_list:
            run_idx += 1
            sql = f'SELECT * FROM {table} WHERE "Mmsi" = {mmsi} ORDER BY "Date"'
            
            try:
                duration_ms, row_count, qid, telem = execute_query_with_telemetry(conn, sql)
                
                run_record = {
                    "run_index": run_idx,
                    "query_family": "Q4",
                    "file_size_mib": fs,
                    "mmsi": mmsi,
                    "sql": sql,
                    "duration_ms": duration_ms,
                    "row_count": row_count,
                    "status": "FINISHED",
                    "query_id": qid,
                    **telem,
                }
                
                results_by_variant[fs].append(run_record)
                all_runs.append(run_record)
                raw_file.write(json.dumps(run_record, ensure_ascii=False) + "\n")
                raw_file.flush()

                if run_idx % 25 == 0 or run_idx == total_expected:
                    log.info(f"  Progress: {run_idx}/{total_expected} (fs={fs} MiB, mmsi={mmsi} -> {duration_ms:.1f} ms, rows={row_count})")

            except Exception as e:
                log.error(f"  FAILED run #{run_idx} (fs={fs} MiB, mmsi={mmsi}): {e}")
                failed_count += 1
                fail_record = {
                    "run_index": run_idx,
                    "query_family": "Q4",
                    "file_size_mib": fs,
                    "mmsi": mmsi,
                    "sql": sql,
                    "status": "FAILED",
                    "error": str(e),
                }
                all_runs.append(fail_record)
                raw_file.write(json.dumps(fail_record, ensure_ascii=False) + "\n")
                raw_file.flush()

    raw_file.close()
    conn.close()
    wall_time_total = time.perf_counter() - start_all

    # Rangkuman statistik per varian ukuran file
    summary_by_variant = {}
    for fs in FILE_SIZES:
        runs = results_by_variant[fs]
        lats = [r["duration_ms"] for r in runs if r.get("duration_ms")]
        bytes_in = [r["physical_input_bytes"] for r in runs if r.get("physical_input_bytes")]
        splits = [r["completed_splits"] for r in runs if r.get("completed_splits")]
        
        summary_by_variant[f"{fs}mib"] = {
            "file_size_mib": fs,
            "total_runs": len(runs),
            "median_latency_ms": round(median(lats), 2) if lats else 0,
            "mean_latency_ms": round(mean(lats), 2) if lats else 0,
            "median_physical_input_bytes": round(median(bytes_in), 2) if bytes_in else 0,
            "mean_completed_splits": round(mean(splits), 2) if splits else 0,
        }

    report = {
        "milestone": "H13_Q4_ENTITY_ROBUSTNESS",
        "benchmark_finished_at": datetime.now(timezone.utc).isoformat(),
        "wall_time_seconds": round(wall_time_total, 2),
        "total_runs_planned": total_expected,
        "total_runs_completed": len(all_runs) - failed_count,
        "failed_runs": failed_count,
        "mmsi_samples_evaluated": len(mmsi_list),
        "file_sizes_evaluated": FILE_SIZES,
        "raw_log_path": str(OUTPUT_RAW_LOG),
        "summary_by_variant": summary_by_variant,
    }

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Laporan ringkasan Q4 tersimpan di: {OUTPUT_REPORT}")

    print()
    print("=" * 60)
    print("BENCHMARK Q4 ENTITY ROBUSTNESS SELESAI (H13)")
    print(f"  Total Runs Selesai : {len(all_runs) - failed_count}/{total_expected}")
    print(f"  Kueri Gagal        : {failed_count}")
    print(f"  Wall Time          : {wall_time_total:.1f} detik")
    print(f"  Raw Log Tersimpan  : {OUTPUT_RAW_LOG}")
    print(f"  Ringkasan Laporan  : {OUTPUT_REPORT}")
    print("  Perbandingan Latensi Median Q4:")
    for k, v in summary_by_variant.items():
        print(f"    - {k:>6s}: {v['median_latency_ms']:>8.2f} ms | Splits rata-rata: {v['mean_completed_splits']:>5.1f}")
    print("=" * 60)

if __name__ == "__main__":
    run_q4_benchmark()
