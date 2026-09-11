"""
Pengukuran Noise Floor Sistem (Gate G7).
Mengeksekusi query baseline ringan 30 kali ke Trino untuk mengukur
variabilitas alami sistem (Coefficient of Variation / CV).
"""
import time
import json
from pathlib import Path
import requests
import numpy as np

TRINO_URL = "http://localhost:8080/v1/statement"
TRINO_USER = "dsic2604"
ITERATIONS = 30
OUTPUT_PATH = Path("data/manifests/gate_g7_noise_floor_report.json")

def run_single_query(session: requests.Session) -> float:
    """Jalankan query ringan 'SELECT 1' dan ukur total waktu eksekusinya (ms)."""
    start_time = time.perf_counter()
    resp = session.post(
        TRINO_URL,
        headers={"X-Trino-User": TRINO_USER},
        data="SELECT 1",
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    
    # Tunggu query hingga selesai jika Trino memberikan nextUri
    while "nextUri" in data:
        time.sleep(0.05)
        resp = session.get(data["nextUri"], timeout=10)
        resp.raise_for_status()
        data = resp.json()

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return elapsed_ms

def main():
    print(f"🚀 Memulai pengukuran Noise Floor Trino ({ITERATIONS} iterasi)...")
    latencies = []
    session = requests.Session()

    # Warm-up run (1x agar engine Trino memuat class/koneksi awal)
    print("⏳ Menjalankan 1x warm-up...")
    run_single_query(session)

    print("📊 Mengambil sampel latency...")
    for i in range(1, ITERATIONS + 1):
        lat = run_single_query(session)
        latencies.append(lat)
        print(f"   Iterasi {i:02d}/{ITERATIONS}: {lat:.2f} ms")
        time.sleep(0.1)  # Jeda singkat antar-query

    latencies_arr = np.array(latencies)
    mean_val = float(np.mean(latencies_arr))
    std_val = float(np.std(latencies_arr, ddof=1))
    cv_percent = (std_val / mean_val) * 100.0 if mean_val > 0 else 0.0

    report = {
        "gate": "G7",
        "metric": "noise_floor",
        "iterations": ITERATIONS,
        "latencies_ms": [round(x, 2) for x in latencies],
        "statistics": {
            "min_ms": round(float(np.min(latencies_arr)), 2),
            "max_ms": round(float(np.max(latencies_arr)), 2),
            "mean_ms": round(mean_val, 2),
            "std_ms": round(std_val, 2),
            "p50_ms": round(float(np.percentile(latencies_arr, 50)), 2),
            "p95_ms": round(float(np.percentile(latencies_arr, 95)), 2),
            "coefficient_of_variation_percent": round(cv_percent, 2),
        },
        "status": "PASSED" if cv_percent < 25.0 else "WARNING_HIGH_VARIABILITY",
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*50)
    print(f"✅ Pengukuran Selesai!")
    print(f"   Rata-rata (Mean) : {mean_val:.2f} ms")
    print(f"   Standar Deviasi  : {std_val:.2f} ms")
    print(f"   Noise Floor (CV) : {cv_percent:.2f} %")
    print(f"   Status Gate G7   : {report['status']}")
    print(f"   Laporan disimpan : {OUTPUT_PATH}")
    print("="*50)

if __name__ == "__main__":
    main()
