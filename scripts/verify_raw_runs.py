"""Audit dan verifikasi integritas data mentah & kelengkapan telemetri (H10).

Memeriksa berkas results/raw/runs.jsonl terhadap:
1. Total runs (harus tepat 1.584 = 144 warmup + 1.440 measured).
2. Kelengkapan 72 kondisi faktorial (masing-masing 2 warmup + 20 measured).
3. Status eksekusi (100% FINISHED, 0 FAILED).
4. Kelengkapan telemetri (missing_metrics kosong pada setiap baris).
5. Validitas nilai metrik (latensi > 0, cpu_ms >= 0, physical_bytes > 0, split > 0).
6. Konsistensi output row_count antar ukuran file.

Deliverable:
  data/manifests/gate_h10_telemetry_report.json
"""
import sys
import json
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

RAW_LOG_PATH = Path("results/raw/runs.jsonl")
OUTPUT_REPORT = Path("data/manifests/gate_h10_telemetry_report.json")

EXPECTED_CONDITIONS = 72
EXPECTED_WARMUP_PER_COND = 2
EXPECTED_MEASURED_PER_COND = 20
EXPECTED_TOTAL_RUNS = EXPECTED_CONDITIONS * (EXPECTED_WARMUP_PER_COND + EXPECTED_MEASURED_PER_COND) # 1584

def verify_raw_runs():
    log.info("=== H10: AUDIT INTEGRITAS RAW RUNS & TELEMETRI ===")

    if not RAW_LOG_PATH.exists():
        log.error(f"File log mentah tidak ditemukan: {RAW_LOG_PATH}")
        sys.exit(1)

    runs = []
    with open(RAW_LOG_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError as e:
                log.error(f"Gagal parse JSON baris {line_num}: {e}")
                sys.exit(1)

    total_runs = len(runs)
    log.info(f"1. Membaca raw runs: {total_runs} baris")

    # 1. Verifikasi Total Runs
    warmup_runs = [r for r in runs if r.get("run_type") == "warmup"]
    measured_runs = [r for r in runs if r.get("run_type") == "measured"]
    
    total_valid = (total_runs == EXPECTED_TOTAL_RUNS)
    warmup_valid = (len(warmup_runs) == EXPECTED_CONDITIONS * EXPECTED_WARMUP_PER_COND)
    measured_valid = (len(measured_runs) == EXPECTED_CONDITIONS * EXPECTED_MEASURED_PER_COND)

    log.info(f"   - Total runs: {total_runs} (Target: {EXPECTED_TOTAL_RUNS}) -> {'PASS' if total_valid else 'FAIL'}")
    log.info(f"   - Warmup runs: {len(warmup_runs)} (Target: 144) -> {'PASS' if warmup_valid else 'FAIL'}")
    log.info(f"   - Measured runs: {len(measured_runs)} (Target: 1440) -> {'PASS' if measured_valid else 'FAIL'}")

    # 2. Verifikasi Distribusi Kondisi Faktorial
    cond_counts = defaultdict(lambda: {"warmup": 0, "measured": 0})
    for r in runs:
        cond = r.get("condition", {})
        key = (cond.get("file_size_mib"), cond.get("query_family"), str(cond.get("selectivity_id")))
        rtype = r.get("run_type")
        cond_counts[key][rtype] += 1

    unique_conditions = len(cond_counts)
    log.info(f"2. Memeriksa 72 kondisi faktorial unik: ditemukan {unique_conditions} kondisi")

    imbalanced_conditions = []
    for key, counts in cond_counts.items():
        if counts["warmup"] != EXPECTED_WARMUP_PER_COND or counts["measured"] != EXPECTED_MEASURED_PER_COND:
            imbalanced_conditions.append({
                "condition": key,
                "counts": counts
            })

    cond_valid = (unique_conditions == EXPECTED_CONDITIONS and len(imbalanced_conditions) == 0)
    log.info(f"   - Keseimbangan repetisi per kondisi: {'PASS (72/72 lengkap)' if cond_valid else f'FAIL ({len(imbalanced_conditions)} tidak seimbang)'}")

    # 3. Verifikasi Status Eksekusi
    failed_runs = [r for r in runs if r.get("status") != "FINISHED" or r.get("state") != "FINISHED"]
    status_valid = (len(failed_runs) == 0)
    log.info(f"3. Verifikasi status FINISHED: {'PASS (0 failed)' if status_valid else f'FAIL ({len(failed_runs)} failed)'}")

    # 4. Verifikasi Telemetri Trino (Missing metrics)
    runs_with_missing_telemetry = []
    for idx, r in enumerate(runs):
        missing = r.get("missing_metrics", [])
        # periksa juga apakah ada field inti bernilai None
        required_fields = ["duration_ms", "cpu_ms", "planning_ms", "physical_input_bytes", "completed_splits", "peak_memory_bytes"]
        null_fields = [f for f in required_fields if r.get(f) is None]
        if missing or null_fields:
            runs_with_missing_telemetry.append({
                "run_index": r.get("run_index", idx),
                "missing": missing,
                "null_fields": null_fields,
            })

    telem_valid = (len(runs_with_missing_telemetry) == 0)
    log.info(f"4. Kelengkapan telemetri Trino: {'PASS (100% lengkap, 0 missing)' if telem_valid else f'FAIL ({len(runs_with_missing_telemetry)} run tidak lengkap)'}")

    # 5. Validitas Nilai Metrik (Sanity Check)
    invalid_metrics = []
    for idx, r in enumerate(runs):
        dur = r.get("duration_ms", 0)
        cpu = r.get("cpu_ms", 0)
        bytes_in = r.get("physical_input_bytes", 0)
        splits = r.get("completed_splits", 0)
        
        if dur <= 0 or cpu < 0 or bytes_in <= 0 or splits <= 0:
            invalid_metrics.append({
                "run_index": r.get("run_index", idx),
                "duration_ms": dur,
                "cpu_ms": cpu,
                "physical_input_bytes": bytes_in,
                "completed_splits": splits,
            })

    sanity_valid = (len(invalid_metrics) == 0)
    log.info(f"5. Pemeriksaan kewajaran nilai metrik: {'PASS (semua metrik valid)' if sanity_valid else f'FAIL ({len(invalid_metrics)} anomali)'}")

    # 6. Konsistensi Hasil Kueri (row_count per query family)
    # kueri yang sama harus mengembalikan row_count yang sama di seluruh varian ukuran file
    row_count_map = defaultdict(set)
    for r in measured_runs:
        cond = r.get("condition", {})
        query_key = (cond.get("query_family"), str(cond.get("selectivity_id")))
        row_count_map[query_key].add(r.get("row_count"))

    inconsistent_row_counts = {str(k): list(v) for k, v in row_count_map.items() if len(v) > 1}
    row_count_valid = (len(inconsistent_row_counts) == 0)
    log.info(f"6. Konsistensi row_count antar varian file: {'PASS (100% identik)' if row_count_valid else f'FAIL ({len(inconsistent_row_counts)} inkonsisten)'}")

    # Evaluasi Gate H10
    gate_passed = (
        total_valid and warmup_valid and measured_valid and
        cond_valid and status_valid and telem_valid and
        sanity_valid and row_count_valid
    )

    report = {
        "gate": "H10_TELEMETRY_AND_RAW_LOG_INTEGRITY",
        "gate_passed": gate_passed,
        "raw_log_path": str(RAW_LOG_PATH.resolve()),
        "summary": {
            "total_runs": total_runs,
            "warmup_runs": len(warmup_runs),
            "measured_runs": len(measured_runs),
            "unique_conditions": unique_conditions,
            "failed_runs": len(failed_runs),
            "missing_telemetry_runs": len(runs_with_missing_telemetry),
            "metric_sanity_anomalies": len(invalid_metrics),
            "inconsistent_row_counts": len(inconsistent_row_counts),
        },
        "checks": {
            "total_runs_check": total_valid,
            "condition_distribution_check": cond_valid,
            "execution_status_check": status_valid,
            "telemetry_completeness_check": telem_valid,
            "metric_sanity_check": sanity_valid,
            "row_count_consistency_check": row_count_valid,
        },
        "details": {
            "imbalanced_conditions": imbalanced_conditions,
            "runs_with_missing_telemetry": runs_with_missing_telemetry,
            "invalid_metrics": invalid_metrics,
            "inconsistent_row_counts": inconsistent_row_counts,
        }
    }

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Laporan verifikasi H10 tersimpan di: {OUTPUT_REPORT}")

    print()
    print("=" * 60)
    print("HASIL AUDIT GATE H10: " + ("LULUS (100% PASS)" if gate_passed else "GAGAL (FAILED)"))
    print(f"  Total Runs Terverifikasi : {total_runs}/1584")
    print(f"  Kondisi Faktorial        : {unique_conditions}/72 (seimbang)")
    print(f"  Status Gagal (Failed)    : {len(failed_runs)}")
    print(f"  Telemetri Hilang         : {len(runs_with_missing_telemetry)}")
    print(f"  Konsistensi Output       : {'100% Identik' if row_count_valid else 'Ada inkonsistensi'}")
    print("=" * 60)

    if not gate_passed:
        sys.exit(1)

if __name__ == "__main__":
    verify_raw_runs()
