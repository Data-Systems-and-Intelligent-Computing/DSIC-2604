"""
H15: Analisis Paired Difference vs Baseline (32 MiB) dan Evaluasi Crossover
============================================================================
Tujuan:
  1. Hitung paired latency difference per repetisi blok:
       Δ(x, b) = latency(file_size=x, block=b) - latency(file_size=32 MiB, block=b)
     untuk setiap (x ≠ 32 MiB, query_family, selectivity_id, block_index)
  2. Hitung statistik ringkasan perbedaan: mean_delta, median_delta, P5-P95 CI empiris
  3. Evaluasi kriteria crossover (protocol_freeze.yaml x crossover.yaml):
     - "Sign change" antara selectivity rendah → tinggi dalam satu query family
     - Direplikasi lintas minimal 2 dari 3 query families (Q1, Q2, Q3)
  4. Simpan:
     - results/tables/paired_diff_table.csv     → tabel per repetisi
     - results/tables/paired_diff_summary.csv   → tabel agregat ringkasan
     - data/manifests/crossover_eval.json        → laporan evaluasi crossover

Input:
  - results/raw/runs_frozen.jsonl
  - configs/crossover.yaml

Output:
  - results/tables/paired_diff_table.csv
  - results/tables/paired_diff_summary.csv
  - data/manifests/crossover_eval.json
"""

import json
import logging
import math
import os
import csv
import yaml
from collections import defaultdict
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Setup logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
FROZEN_JSONL = os.path.join("results", "raw", "runs_frozen.jsonl")
CROSSOVER_YAML = os.path.join("configs", "crossover.yaml")
OUT_PAIRED_DIFF = os.path.join("results", "tables", "paired_diff_table.csv")
OUT_PAIRED_SUMMARY = os.path.join("results", "tables", "paired_diff_summary.csv")
OUT_CROSSOVER = os.path.join("data", "manifests", "crossover_eval.json")

os.makedirs(os.path.join("results", "tables"), exist_ok=True)
os.makedirs(os.path.join("data", "manifests"), exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Baca konfigurasi crossover
# ---------------------------------------------------------------------------
log.info("=== H15: ANALISIS PAIRED DIFFERENCE & EVALUASI CROSSOVER ===")
with open(CROSSOVER_YAML, encoding="utf-8") as f:
    raw_yaml = yaml.safe_load(f)

cfg = raw_yaml.get("crossover", raw_yaml)  # toleran: top-level atau nested
BASELINE_MIB = int(cfg.get("baseline_file_size_mib", 32))
CONFIDENCE_LEVEL = float(cfg.get("confidence_level", 0.95))
REQUIRE_SIGN_CHANGE = bool(cfg.get("require_sign_change", True))
REQUIRE_REPLICATION = bool(cfg.get("require_replicated_direction_across_main_query_family", True))
log.info(
    f"Config crossover: baseline={BASELINE_MIB} MiB, CI={CONFIDENCE_LEVEL:.0%}, "
    f"require_sign_change={REQUIRE_SIGN_CHANGE}, require_replication={REQUIRE_REPLICATION}"
)

# ---------------------------------------------------------------------------
# 2. Baca runs_frozen.jsonl — hanya measured runs
# ---------------------------------------------------------------------------
log.info(f"1. Membaca {FROZEN_JSONL} ...")
all_runs = []
with open(FROZEN_JSONL, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r.get("run_type") == "measured":
            all_runs.append(r)
log.info(f"   -> {len(all_runs)} measured runs dimuat")

# Bangun indeks: (file_size_mib, query_family, selectivity_id, block_index) -> latency_ms
index = {}
for r in all_runs:
    cond = r["condition"]
    key = (
        int(cond["file_size_mib"]),
        cond["query_family"],
        cond["selectivity_id"],
        int(r["block_index"]),
    )
    if key in index:
        raise ValueError(f"Kunci duplikat: {key}")
    index[key] = float(r["duration_ms"])

log.info(f"   -> Indeks dibangun: {len(index)} entri unik")

# ---------------------------------------------------------------------------
# 3. Hitung paired difference Δ per blok
# ---------------------------------------------------------------------------
log.info("2. Menghitung paired difference Δ = latency(x) - latency(32 MiB) per blok ...")

# Daftar dimensi
file_sizes = sorted(set(k[0] for k in index.keys()))
query_families = sorted(set(k[1] for k in index.keys()))
selectivity_ids = sorted(set(k[2] for k in index.keys()), key=lambda x: float(x))
block_indices = sorted(set(k[3] for k in index.keys()))

non_baseline_sizes = [s for s in file_sizes if s != BASELINE_MIB]
log.info(f"   File sizes: {file_sizes}, Baseline: {BASELINE_MIB} MiB")
log.info(f"   Non-baseline sizes: {non_baseline_sizes}")
log.info(f"   Query families: {query_families}, Selectivities: {selectivity_ids}")
log.info(f"   Blocks: {block_indices[0]}–{block_indices[-1]} ({len(block_indices)} blok)")

# Hitung Δ per baris
paired_rows = []
for fs in non_baseline_sizes:
    for qf in query_families:
        for sel in selectivity_ids:
            for blk in block_indices:
                key_x = (fs, qf, sel, blk)
                key_base = (BASELINE_MIB, qf, sel, blk)
                if key_x not in index or key_base not in index:
                    log.warning(f"Data hilang untuk pair: x={key_x}, base={key_base}")
                    continue
                lat_x = index[key_x]
                lat_base = index[key_base]
                delta = lat_x - lat_base
                paired_rows.append({
                    "file_size_mib": fs,
                    "query_family": qf,
                    "selectivity_id": sel,
                    "block_index": blk,
                    "latency_x_ms": round(lat_x, 4),
                    "latency_baseline_ms": round(lat_base, 4),
                    "delta_ms": round(delta, 4),
                })

log.info(f"   -> {len(paired_rows)} baris paired difference dihitung")

# ---------------------------------------------------------------------------
# 4. Simpan paired_diff_table.csv
# ---------------------------------------------------------------------------
log.info(f"3. Menyimpan tabel paired difference ke: {OUT_PAIRED_DIFF}")
fieldnames_diff = [
    "file_size_mib", "query_family", "selectivity_id", "block_index",
    "latency_x_ms", "latency_baseline_ms", "delta_ms",
]
with open(OUT_PAIRED_DIFF, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_diff)
    writer.writeheader()
    writer.writerows(paired_rows)

# ---------------------------------------------------------------------------
# 5. Hitung ringkasan statistik per (file_size, query_family, selectivity)
# ---------------------------------------------------------------------------
log.info("4. Menghitung ringkasan statistik per (ukuran file × query family × selektivitas) ...")


def _percentile(sorted_data, pct):
    """Percentile interpolasi linier (sama dengan numpy percentile metode 'linear')."""
    n = len(sorted_data)
    if n == 0:
        return float("nan")
    if n == 1:
        return sorted_data[0]
    rank = pct / 100.0 * (n - 1)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return sorted_data[lo]
    return sorted_data[lo] + (rank - lo) * (sorted_data[hi] - sorted_data[lo])


# Kelompokkan delta per (fs, qf, sel)
groups = defaultdict(list)
for row in paired_rows:
    key = (row["file_size_mib"], row["query_family"], row["selectivity_id"])
    groups[key].append(row["delta_ms"])

summary_rows = []
for (fs, qf, sel), deltas in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1], float(x[0][2]))):
    n = len(deltas)
    sorted_d = sorted(deltas)
    mean_d = sum(deltas) / n
    median_d = _percentile(sorted_d, 50)
    p5_d = _percentile(sorted_d, 5)
    p95_d = _percentile(sorted_d, 95)
    std_d = math.sqrt(sum((d - mean_d) ** 2 for d in deltas) / n)
    # Tanda: negatif = x lebih CEPAT dari baseline; positif = x lebih LAMBAT
    sign_negative = sum(1 for d in deltas if d < 0)
    sign_positive = sum(1 for d in deltas if d > 0)
    dominant_sign = "negative" if sign_negative > sign_positive else "positive" if sign_positive > sign_negative else "tie"
    summary_rows.append({
        "file_size_mib": fs,
        "query_family": qf,
        "selectivity_id": sel,
        "n_blocks": n,
        "mean_delta_ms": round(mean_d, 4),
        "median_delta_ms": round(median_d, 4),
        "std_delta_ms": round(std_d, 4),
        "p5_delta_ms": round(p5_d, 4),
        "p95_delta_ms": round(p95_d, 4),
        "pct_negative": round(100 * sign_negative / n, 1),
        "dominant_sign": dominant_sign,
    })

log.info(f"   -> {len(summary_rows)} baris ringkasan dihasilkan")

# ---------------------------------------------------------------------------
# 6. Simpan paired_diff_summary.csv
# ---------------------------------------------------------------------------
log.info(f"5. Menyimpan ringkasan ke: {OUT_PAIRED_SUMMARY}")
fieldnames_summary = [
    "file_size_mib", "query_family", "selectivity_id", "n_blocks",
    "mean_delta_ms", "median_delta_ms", "std_delta_ms",
    "p5_delta_ms", "p95_delta_ms", "pct_negative", "dominant_sign",
]
with open(OUT_PAIRED_SUMMARY, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_summary)
    writer.writeheader()
    writer.writerows(summary_rows)

# ---------------------------------------------------------------------------
# 7. Evaluasi Crossover per (file_size × query_family)
# ---------------------------------------------------------------------------
log.info("6. Mengevaluasi kriteria crossover ...")

# Crossover: terjadi ketika median_delta berubah tanda (dari negatif ke positif
# atau sebaliknya) seiring naiknya selectivity dalam satu (file_size, query_family)
selectivities_ordered = sorted(set(r["selectivity_id"] for r in summary_rows), key=lambda x: float(x))

crossover_details = {}
crossover_per_qf = defaultdict(dict)  # {qf: {fs: has_crossover}}

for fs in non_baseline_sizes:
    for qf in query_families:
        # Ambil median_delta terurut berdasarkan selectivity
        series = []
        for sel in selectivities_ordered:
            match = next(
                (r for r in summary_rows if r["file_size_mib"] == fs and r["query_family"] == qf and r["selectivity_id"] == sel),
                None,
            )
            if match:
                series.append((float(sel), match["median_delta_ms"], match["dominant_sign"]))

        # Cek sign change: apakah ada pergantian tanda di median_delta antar selectivity?
        signs = [s[2] for s in series]
        has_sign_change = False
        crossover_sel = None
        for i in range(1, len(signs)):
            if signs[i - 1] != signs[i] and signs[i - 1] in ("negative", "positive") and signs[i] in ("negative", "positive"):
                has_sign_change = True
                crossover_sel = series[i][0]
                break

        # Tentukan ranking dominan di selektivitas rendah vs tinggi
        low_sel = series[0] if series else None   # selectivity terendah
        high_sel = series[-1] if series else None  # selectivity tertinggi
        low_faster = low_sel and low_sel[1] < 0   # x lebih cepat di sel. rendah
        high_faster = high_sel and high_sel[1] < 0  # x lebih cepat di sel. tinggi

        key = f"{fs}mib_{qf}"
        crossover_details[key] = {
            "file_size_mib": fs,
            "query_family": qf,
            "has_sign_change": has_sign_change,
            "crossover_selectivity": crossover_sel,
            "series": [
                {"selectivity": s[0], "median_delta_ms": s[1], "dominant_sign": s[2]}
                for s in series
            ],
            "low_sel_x_faster_than_baseline": bool(low_faster),
            "high_sel_x_faster_than_baseline": bool(high_faster),
        }
        crossover_per_qf[qf][fs] = has_sign_change

# Evaluasi crossover global: harus terlihat di ≥ 2 dari 3 query families (jika REQUIRE_REPLICATION)
crossover_per_size = {}
for fs in non_baseline_sizes:
    qf_with_crossover = [qf for qf in query_families if crossover_per_qf[qf].get(fs, False)]
    n_qf_crossover = len(qf_with_crossover)
    if REQUIRE_REPLICATION:
        crossover_confirmed = n_qf_crossover >= 2
    else:
        crossover_confirmed = n_qf_crossover >= 1
    crossover_per_size[str(fs)] = {
        "file_size_mib": fs,
        "n_query_families_with_crossover": n_qf_crossover,
        "query_families_with_crossover": qf_with_crossover,
        "crossover_confirmed": crossover_confirmed,
    }
    status_str = "✅ CONFIRMED" if crossover_confirmed else "❌ NOT CONFIRMED"
    log.info(
        f"   {fs} MiB vs {BASELINE_MIB} MiB: crossover di {n_qf_crossover}/3 query families → {status_str}"
    )

any_crossover = any(v["crossover_confirmed"] for v in crossover_per_size.values())

# ---------------------------------------------------------------------------
# 8. Simpan crossover_eval.json
# ---------------------------------------------------------------------------
report = {
    "script": "scripts/analyze_paired_diff_h15.py",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "config": {
        "baseline_file_size_mib": BASELINE_MIB,
        "confidence_level": CONFIDENCE_LEVEL,
        "require_sign_change": REQUIRE_SIGN_CHANGE,
        "require_replication_across_query_families": REQUIRE_REPLICATION,
    },
    "inputs": {
        "runs_frozen_jsonl": FROZEN_JSONL,
        "measured_runs": len(all_runs),
        "paired_rows": len(paired_rows),
    },
    "outputs": {
        "paired_diff_table": OUT_PAIRED_DIFF,
        "paired_diff_summary": OUT_PAIRED_SUMMARY,
    },
    "crossover_per_size": crossover_per_size,
    "crossover_per_qf_x_size": crossover_details,
    "overall_result": {
        "any_crossover_confirmed": any_crossover,
        "verdict": "CROSSOVER_DETECTED" if any_crossover else "NO_CROSSOVER",
        "hypothesis_H2_direction": "SUPPORTED" if any_crossover else "NOT_SUPPORTED",
    },
}

with open(OUT_CROSSOVER, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

log.info(f"7. Laporan crossover tersimpan di: {OUT_CROSSOVER}")

# ---------------------------------------------------------------------------
# Ringkasan akhir
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("HASIL ANALISIS H15: PAIRED DIFFERENCE & CROSSOVER")
print(f"  Paired rows dihitung : {len(paired_rows)} baris")
print(f"  Ringkasan kondisi    : {len(summary_rows)} kondisi")
print()
print("  Evaluasi Crossover (vs baseline 32 MiB):")
for fs_str, info in sorted(crossover_per_size.items(), key=lambda x: int(x[0])):
    status = "CONFIRMED ✅" if info["crossover_confirmed"] else "NOT CONFIRMED ❌"
    print(
        f"    {int(fs_str):>3} MiB : {info['n_query_families_with_crossover']}/3 query family → {status}"
    )
print()
verdict = report["overall_result"]["verdict"]
h2 = report["overall_result"]["hypothesis_H2_direction"]
print(f"  Verdict Crossover Global : {verdict}")
print(f"  Hipotesis H2 (Crossover) : {h2}")
print(f"  Paired Diff Table : {OUT_PAIRED_DIFF}")
print(f"  Paired Diff Summary : {OUT_PAIRED_SUMMARY}")
print(f"  Crossover Report  : {OUT_CROSSOVER}")
print("=" * 60)
