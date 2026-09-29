# Catatan Minggu 4 — Reproduksi, Ekstensi, dan Manuskrip (H22–H28)

## Konteks & Latar Belakang
Minggu 1 (H1–H7), Minggu 2 (H8–H14), dan Minggu 3 (H15–H21) telah tuntas 100%:
- **Minggu 1:** Protokol dibekukan, dataset MMDEC divalidasi integritasnya, stack Docker lakehouse (Trino + Iceberg REST + MinIO) terverifikasi, 4 varian Parquet (`ais_pos_08`, `16`, `32`, `64`) terpisah secara IQR dengan row-group seragam (~8 MiB), 6 band selektivitas terkalibrasi, dan noise floor terukur (CV 7.83%).
- **Minggu 2:** Main Factorial Benchmark E3 dieksekusi penuh (1.584 run, 0 gagal, 100% telemetri lengkap) dan disegel dengan SHA-256 di `results/raw/runs_frozen.jsonl`.
- **Minggu 3:** Analisis statistik mendalam (Paired Difference, Bootstrap 95% BCa, Mechanism Attribution, Failure Analysis, Row-Order Robustness, dan Write Guardrail ROI) selesai dan dipaketkan ke dalam *Results v1 Freeze*.

**Fokus Minggu 4:** Membuktikan reproduksibilitas bersih (*Clean-Slate Reproduction* / H22), mengevaluasi uji ekstensi/secondary jika diperlukan, memverifikasi literatur bebas over-claiming, serta menyusun bab-bab manuskrip skripsi/artikel ilmiah.

---

## 🗺️ Rencana Kerja Minggu 4 (H22–H28)

| Hari | Fokus | Eksperimen | Target Deliverable / Gate | Status |
|:---:|:---|:---|:---|:---:|
| **H22** | Clean-Slate Reproduction | E5 (Audit Determinisme) | `gate_h22_reproduction_report.json` | ✅ Selesai (Gate H22 LULUS, Deviasi 2.31%) |
| **H23** | Secondary Table (Empiris Penuh) | E5 (External Robustness) | `gate_h23_secondary_report.json` | ✅ Selesai (Gate H23 LULUS, Speedup 1.79x, rho=1.00) |
| **H24** | Mixed Workload Decision Map | E6 (Held-out Trace) | Figure 15 + `gate_h24_mixed_workload_report.json` | ✅ Selesai (Gate H24 LULUS, Figure 15 Terbit) |
| **H25** | Final Related Work & Literature | Manuskrip | Sinkronisasi sitasi & hapus over-claiming | ⚪ Direncanakan |
| **H26** | Penulisan Bab Metodologi & Testbed | Manuskrip | Naskah BAB 3 lengkap | ⚪ Direncanakan |
| **H27** | Penulisan Bab Hasil & Pembahasan | Manuskrip | Naskah BAB 4 lengkap | ⚪ Direncanakan |
| **H28** | Penulisan Bab Penutup & Final Artifact | Manuskrip / Release | Naskah BAB 5, Abstrak & Artefak v1.0 | ⚪ Direncanakan |

---

## 📋 H24 — Mixed Workload Decision Map (Eksperimen E6 / Figure 15)

- **Tujuan:**  
  Mengevaluasi efisiensi operasional dari Peta Keputusan Kondisional (*Selectivity-Aware Workload Mapping*) terhadap strategi statis (Fixed 8, 16, 32, 64 MiB) pada beban kerja campuran realistis (*stream of 1,000 queries*, bebas kebocoran dari data kalibrasi).
- **Prosedur:**
  1. Bangun 2 profil jejak beban kerja (*held-out synthetic workload traces*):
     - **Trace 1 (Monitoring-Heavy):** $70\%$ selektivitas rendah, $25\%$ sedang, $5\%$ tinggi.
     - **Trace 2 (Analytical-Heavy):** $30\%$ selektivitas rendah/sedang, $70\%$ selektivitas tinggi.
  2. Simulasikan eksekusi 5 strategi layout terhadap batas teoretis *Oracle Best*.
  3. Hitung akumulasi latensi kerja, speedup vs baseline 32 MiB, total regret, dan kurva amortisasi biaya tulis (*write guardrail*).
- **Temuan Kunci:**
  - **Speedup Lintas Beban:** Strategi *Selectivity-Aware* memberikan speedup **$1.23\times$** pada beban monitoring (memangkas latensi dari 214.8s ke 175.2s) dan **$1.10\times$** pada beban analitik (dari 322.0s ke 293.5s).
  - **Regret Terendah:** Regret strategi adaptif mendekati nol relatif terhadap baseline statis.
  - **Break-Even Amortisasi:** Biaya penulisan layout teramortisasi penuh (*break-even*) hanya dalam **$< 200$ kueri**.
- **Deliverables:**
  - **Figure 15:** `results/figures/fig15_mixed_workload_decision_map.png` & `.pdf` (3 Panel Publikasi Ilmiah).
  - **Tabel:** `results/tables/mixed_workload_benchmark_table.csv`.
  - **Manifest Audit:** `data/manifests/gate_h24_mixed_workload_report.json`.
- **Status Quality Gate H24:** **LULUS (PASSED 100%)**.

---

## 📋 H23 — Secondary Table External Robustness (Dataset_AIS_SPEC)

- **Tujuan:**  
  Membuktikan validitas eksternal (External Robustness / RQ5) bahwa temuan interaksi ukuran file dan selektivitas tidak terbatas pada tabel `AIS_POS`, melainkan dapat digeneralisasi pada tabel sekunder MMDEC (`Dataset_AIS_SPEC.parquet`: 13.558.007 baris, 19 kolom, ~210 MiB compressed).
- **Prosedur:**
  1. Unduh dan validasi data kanonik sekunder dari Zenodo (`Dataset_AIS_SPEC.parquet`, MD5 cocok 100%, 13.558.007 baris).
  2. Bangun 4 varian layout Parquet terkontrol (`ais_spec_08`, `ais_spec_16`, `ais_spec_32`, `ais_spec_64`) dengan row-group 8 MiB, Snappy, date-clustered.
  3. Daftarkan ke Iceberg REST Catalog dan ukur biaya penulisan ke `data/manifests/secondary_write_cost_manifest.csv`.
  4. Eksekusi benchmark 12 kondisi faktorial representatif (4 ukuran file $\times$ 3 band selektivitas: S1, S4, S6) dengan 3 warm-up + 10 measured repetitions.
- **Temuan Kunci:**
  - **Selektivitas Rendah (S1 ~0.1%):** Varian 8 MiB (100.8 ms) mengungguli 64 MiB (180.8 ms) dengan speedup **1.79x**, dan urutan latensi monotonik sempurna ($\rho = 1.0000$, $p < 0.001$) akibat efektivitas data skipping.
  - **Selektivitas Tinggi (S6 ~76%):** Superioritas 8 MiB menyempit drastis akibat amortisasi split overhead.
- **Deliverables:**
  - `data/manifests/source_manifest.csv` (tercatat `Dataset_AIS_SPEC.parquet`)
  - `data/manifests/secondary_write_cost_manifest.csv`
  - `results/tables/h23_secondary_benchmark_results.csv`
  - `data/manifests/gate_h23_secondary_report.json`
- **Status Quality Gate H23:** **LULUS (PASSED 100%)**.

---

## 📋 H22 — Clean-Slate Reproduction

- **Tujuan:**  
  Membuktikan bahwa seluruh temuan benchmark E3 dan Results v1 bersifat deterministik dan dapat diulang dari awal (*clean redeploy*) tanpa adanya efek samping residu sistem (*system state leakage*).
- **Prosedur:**
  1. Restart/verifikasi stack Docker dan pulihkan metadata katalog via `python scripts/restore_catalog.py`.
  2. Eksekusi 12 kondisi faktorial representatif (4 ukuran file $\times$ 3 selektivitas: $0.01\%$, $5.0\%$, $50.0\%$) via `scripts/run_h22_clean_reproduction.py`.
  3. Bandingkan deviasi relatif terhadap median baseline Results v1 (`runs_frozen.jsonl`).
  4. Syarat Kelulusan Quality Gate H22: Deviasi rata-rata $\le 15.0\%$ (dalam toleransi host/noise floor).
- **Deliverables:**
  - `scripts/run_h22_clean_reproduction.py`
  - `data/manifests/gate_h22_reproduction_report.json`
  - `results/tables/h22_reproduction_comparison.csv`
