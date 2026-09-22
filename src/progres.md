# Log Progres Penelitian DSIC-2604
**Topik:** Interaksi Ukuran Data-File Parquet dan Selektivitas Query pada Lakehouse Bersumber Daya Terbatas: Evaluasi Terkontrol Menggunakan MMDEC  
**Repositori:** [Data-Systems-and-Intelligent-Computing/DSIC-2604](https://github.com/Data-Systems-and-Intelligent-Computing/DSIC-2604)  
**Dataset:** MMDEC (`Dataset_AIS_POS.parquet`) — DOI: [10.5281/zenodo.17491518](https://doi.org/10.5281/zenodo.17491518)  
**Terakhir Diperbarui:** 22 September 2026

---

## ⚠️ Prinsip Kolaborasi & Eksekusi
- **Peran AI / Asisten:** Hanya memberikan instruksi, arahan langkah demi langkah, penjelasan konsep, dan rekomendasi kode/perintah.
- **Peran Pengguna (User):** Mengetik kode, memodifikasi file, dan menjalankan perintah di terminal.
- **Aturan Eksekusi:** AI **TIDAK BOLEH** mengeksekusi skrip/perintah terminal secara mandiri kecuali diminta secara eksplisit oleh Pengguna.

---

## 📌 Status Terkini Proyek
- **Status Sinkronisasi Repo:**
  - Repositori remote GitHub: `Data-Systems-and-Intelligent-Computing/DSIC-2604`.
  - Folder lokal: Ditemukan folder `D:\DSIC-2604` (sudah ter-clone dengan git) dan `D:\Tugas Akhir` (workspace aktif di IDE).
  - Berkas H1 telah dibuat di lokal dan dicatat di GitHub.
- **Fase Aktif:** **Minggu 2 (H8–H14 — Main Factorial Benchmark)**.

---

## 🗺️ Roadmap Eksperimen 4 Minggu

| Minggu | Fokus | Eksperimen | Gate Utama | Status |
|---|---|---|---|---|
| **Minggu 1 (H1–H7)** | Freeze, Data, Infrastruktur, Layout, Pilot | E0, E1, E2 | G1–G9 | ✅ Selesai (H1–H7 ✅) |
| **Minggu 2 (H8–H14)** | Main Factorial Benchmark | E3 | Kelengkapan run & telemetry | ✅ Selesai (H8–H14 ✅) |
| **Minggu 3 (H15–H21)** | Analisis, Mekanisme, Robustness | E4, E5 | Results v1 freeze | ⚪ Belum Dimulai |
| **Minggu 4 (H22–H28)** | Reproduksi, Ekstensi, Manuskrip | E5, E6 | Quality gate skripsi/artikel | ⚪ Belum Dimulai |

---

## 📋 Rincian Progres Minggu 1

### ✅ H1 — Freeze Protokol dan Akuisisi Data (Selesai)
- [x] Bekukan RQ1–RQ5, hipotesis H1–H5, dan novelty boundary di `configs/protocol_freeze.yaml`.
- [x] Unduh MMDEC (`Dataset_AIS_POS.parquet`), catat tanggal (08 Sept 2026) dan lisensi (CC BY-NC 4.0).
- [x] Hitung SHA-256 (`88998c43f7e152710c3b157cf47c8119cdef05554d2a6d32e980ce36101b5785`).
- [x] Catat ke `data/manifests/source_manifest.csv`.
- [x] Uji kontrak integritas lulus (`tests/test_source_contract.py`).
- **Status Gate:** Terverifikasi H1.

---

### ✅ H2 — Validasi Sumber terhadap Artikel & Ukur Ukuran Tabel Kanonik (Selesai)
- [x] Skrip audit `src/validate_source.py` berhasil dijalankan.
- [x] Validasi row count (`19.014.229` baris) dan MMSI unik (`25.130` kapal) 100% cocok.
- [x] Validasi 14 kolom skema (Tabel 2 artikel MMDEC) dan kolom temporal `Date` (`timestamp[us]`) sah.
- [x] EDA distribusi baris per hari: 93 hari kalender (min: 183, avg: 204.454, median: 209.987, max: 245.324).
- [x] Pengukuran ukuran tabel kanonik:
  - Fisik di disk: `450,05 MiB` (`450.935.970` bytes)
  - Uncompressed: `519,30 MiB` (`544.528.804` bytes)
  - Rasio kompresi: `1,208x` (19 row groups)
  - Signifikansi grid H5: Kondisi 256 MiB menghasilkan < 8 file, menjadi dasar empiris perlunya varian fallback `8/16/32/64 MiB`.
- [x] Deliverable audit tersimpan di `data/manifests/gate_g1_validation_report.json`.
- [x] Catat hasil lengkap ke `progres_minggu_1-4/minggu1/README.md`.
- **Status Gate:** **Gate G1 LULUS 100%**.

---

### ✅ H3 — Deploy Lakehouse & Smoke Test (Selesai)
- [x] Siapkan file lingkungan `.env` berdasarkan `.env.example`.
- [x] Jalankan lakehouse lokal via Docker Compose: `docker compose -f infra/docker-compose.yml --env-file .env up -d`.
  - Service: MinIO (S3 storage), Iceberg REST Catalog, Trino (Query engine).
- [x] Verifikasi bucket dan register skema `dsic2604` ke Iceberg.
- [x] Eksekusi smoke test lulus (Trino + Iceberg REST + MinIO).
- [x] Catat snapshot environment ke `data/manifests/environment_snapshot.yaml`.
- **Status Gate:** **Gate G7 (Part 1 - Environment Freeze) LULUS 100%**.
- **Target Deliverable:** Smoke test lulus + environment snapshot.

---

### ✅ H4 — Freeze Resource dan Ukur Noise Floor (Selesai)
- [x] Bekukan CPU/RAM limit di `.env` dan `docker-compose.yml`.
- [x] Jalankan baseline query ringan 30x untuk menghitung Coeff of Variation (CV) latency.
- [x] Hasil terukur: Mean = 288.99 ms, CV = 7.83% (sangat stabil).
- [x] Deliverable laporan tersimpan di `data/manifests/gate_g7_noise_floor_report.json`.
- **Status Gate:** **Gate G7 LULUS 100%**.
---

### ✅ H5 — Baseline Layout dan Keputusan Grid (Selesai)
- [x] Tentukan target grid: Fallback grid 8/16/32/64 MiB (karena kondisi 256 MiB menghasilkan 1 file < 8 file).
- [x] Catat keputusan dan justifikasi ke `configs/layout.yaml: grid_decision`.
- [x] Eksekusi kontrak uji kelayakan lulus (`tests/test_file_size_separation.py`).
- **Status Gate:** **Gate G3 LULUS 100%**.

---

### ✅ H6 — Generate Varian Parquet dan Audit (Selesai)
- [x] Tulis 4 varian ukuran file dari snapshot kanonik yang sama (`ais_pos_08`, `ais_pos_16`, `ais_pos_32`, `ais_pos_64`):
  - Row-group konstan: target 8 MiB (Snappy compression, unpartitioned, date_clustered_fixed).
  - Row count konsisten 100%: masing-masing tepat 19.014.229 baris.
- [x] Audit separasi IQR dan kontrol ukuran row-group:
  - **Gate G2 (Layout Completeness):** LULUS (4/4 varian terbuat).
  - **Gate G3 (IQR Separation & Feasibility):** LULUS (rasio median berdekatan: 1.85x, 1.92x, 1.82x > 1.5x; tidak ada tumpang-tindih IQR; kondisi terbesar 8 file ≥ 8).
  - **Gate G4 (Row-group Control):** LULUS (spread relatif = 0.2276 ≤ toleransi 0.25).
- [x] Uji kesetaraan semantik kueri (Q1, Q2, Q3) di Trino:
  - Q1 (predicate scan count): 1.576.090 baris (100% identik di 4 varian).
  - Q2 (selective aggregation: avg & max SOG): 100% identik.
  - Q3 (selective group-by MessageType): 100% identik.
  - Seluruh 6 unit test `tests/test_semantic_equivalence.py` lulus.
- [x] Deliverables:
  - `data/manifests/layout_manifest.csv`
  - `data/manifests/write_cost_manifest.csv`
  - `data/manifests/gate_g2g3g4_audit_report.json`
  - `data/manifests/gate_equivalence_report.json`
- **Status Gate:** **Gate G2, G3, G4 LULUS 100%**.

---

### ✅ H7 — Kalibrasi Selectivity dan Pilot Benchmark (Selesai)
- [x] Kalibrasi boundary 6 band selectivity pada tabel baseline (`ais_pos_32`):
  - S1 (0.1%): measured = 0.0893% (rel_err = 10.7%) [LULUS]
  - S2 (1.0%): measured = 0.8987% (rel_err = 10.1%) [LULUS]
  - S3 (5.0%): measured = 4.5521% (rel_err = 9.0%) [LULUS]
  - S4 (20.0%): measured = 17.5434% (rel_err = 12.3%) [LULUS]
  - S5 (50.0%): measured = 45.1344% (rel_err = 9.7%) [LULUS]
  - S6 (90.0%): measured = 76.0963% (rel_err = 15.4%) [LULUS]
  - **Gate G5 (All bands within 20% relative error):** LULUS.
  - **Gate G6 (Monotonically ordered):** LULUS.
  - Deliverables: `data/manifests/selectivity_manifest.csv` dan `data/manifests/gate_g5g6_selectivity_report.json`.
- [x] Uji pilot protokol benchmark (Gate **G8, G9**).
  - Berhasil dibekukan Q1-Q3 di `configs/queries.yaml` dan Q4 di `data/manifests/q4_mmsi_sample.csv`.
  - Durasi Pilot: 176.43 detik.
  - Estimasi total durasi main benchmark: ~4.02 jam.
  - Deliverables: `data/manifests/gate_g8_g9_pilot_report.json`.

---

## 📋 Rincian Progres Minggu 2

### ✅ H8 — Pre-flight Check sebelum Main Run (Selesai)
- [x] Verifikasi kesehatan 3 container Docker (Trino, Iceberg REST, MinIO).
- [x] Buat script restorasi otomatis catalog: `scripts/restore_catalog.py`.
- [x] Spot-check validasi row count 19.014.229 baris di kedua ujung grid (`ais_pos_08` & `ais_pos_64`).
- [x] Konfirmasi config freeze bersih (`git diff` kosong).
- [x] Buat entry point benchmark Windows: `scripts/run_benchmark.py`.
- [x] Dry-run benchmark 72 query lulus tanpa error (wall time: 34.3s).
- [x] Bersihkan direktori `results/raw/` untuk persiapan H9.
- **Status Gate:** Checklist Pre-flight LULUS 100%.

---

### ✅ H9 — Main Factorial Benchmark Run (Selesai)
- [x] Restorasi dan verifikasi 4 tabel Iceberg di Trino (`scripts/restore_catalog.py`).
- [x] Eksekusi main factorial benchmark E3 (`scripts/run_benchmark.py`).
- [x] Selesaikan seluruh 72 kondisi faktorial:
  - 4 ukuran file (8, 16, 32, 64 MiB) × 6 band selektivitas (0.01%–50%) × 3 query families (Q1, Q2, Q3).
  - 2 warm-up runs/kondisi (144 run) + 20 measured repetitions/kondisi (1.440 run) = 1.584 total run.
- [x] Hasil metrik:
  - Total runs: 1.584 (100% finished, 0 failed).
  - Telemetri Trino: 100% lengkap (`missing_telemetry_runs: 0`).
  - Wall time: 458.5 detik (~7,64 menit).
- [x] Deliverables:
  - `results/raw/runs.jsonl` (1.584 baris data mentah JSONL, ukuran ~1,4 MB).
  - `data/manifests/benchmark_summary_report.json`.
  - `src/catatan_belajar.md` (Buku catatan belajar komprehensif riset DSIC-2604).
- **Status Gate:** **Gate Kelengkapan Run & Telemetry LULUS 100%**.

---

### ✅ H10 — Verifikasi Telemetry & Integritas Raw Log (Selesai)
- [x] Buat skrip audit integritas otomatis: `scripts/verify_raw_runs.py`.
- [x] Audit forensik 6 pilar pada `results/raw/runs.jsonl`:
  - Total runs 100% cocok: 1.584 baris (144 warmup + 1.440 measured).
  - Distribusi kondisi 100% seimbang: 72 kondisi faktorial unik (masing-masing 2 warmup + 20 measured).
  - Status eksekusi 100% selesai: 1.584 FINISHED, 0 FAILED.
  - Telemetri Trino 100% lengkap: 0 missing metrics, 0 null fields.
  - Kewajaran metrik (sanity check): seluruh latensi, cpu, bytes, dan splits bernilai positif dan wajar.
  - Konsistensi semantik output: row_count kueri identik di semua ukuran file.
- [x] Deliverables:
  - `scripts/verify_raw_runs.py`.
  - `data/manifests/gate_h10_telemetry_report.json`.
- **Status Gate:** **Gate Telemetry Completeness & Raw Log Integrity LULUS 100%**.

---

### ✅ H11 — Buffer / Catch-up / Re-run Evaluation (Selesai)
- [x] Buat skrip evaluasi buffer otomatis: `scripts/audit_h11_buffer.py`.
- [x] Evaluasi ambang batas re-run terhadap hasil Gate H10:
  - Kegagalan kueri = 0 (Target: 0).
  - Telemetri hilang = 0 (Target: 0).
  - Kondisi timpang = 0 (Target: 0).
  - Anomali nilai = 0 (Target: 0).
- [x] Keputusan: Re-run ditiadakan secara sah (*Zero-Failure state*).
- [x] Deliverables:
  - `scripts/audit_h11_buffer.py`.
  - `data/manifests/h11_buffer_clearance_report.json` (`CLEARED_NO_RERUN_NEEDED`).
- **Status Milestone:** **Buffer Clearance LULUS 100% (CLEARED)**.

---

### ✅ H12 — Freeze Raw Data & Snapshot Checksum (Selesai)
- [x] Buat skrip pembekuan otomatis: `scripts/freeze_raw_data.py`.
- [x] Salin dan kunci data mentah ke berkas permanen: `results/raw/runs_frozen.jsonl`.
- [x] Verifikasi kuantitas data: 1.584 baris utuh, 1.403.827 bytes.
- [x] Hitung sidik jari kriptografis SHA-256 Checksum: `a868d202a03e2d0ff239b32bc4408f2cadf7c33f52adbcd5cf2d31469ae9cc6e`.
- [x] Deliverables:
  - `scripts/freeze_raw_data.py`.
  - `results/raw/runs_frozen.jsonl`.
  - `data/manifests/raw_freeze_manifest.json` (`FROZEN_AND_VERIFIED`).
- **Status Milestone:** **Raw Data Freeze LULUS 100% (FROZEN & VERIFIED)**.

---

### ✅ H13 — Buffer & Out-of-Grid Benchmark (Q4 Entity Robustness) (Selesai)
- [x] Buat skrip eksekutor benchmark Q4: `scripts/run_q4_robustness.py`.
- [x] Eksekusi 200 kueri Q4 terhadap 50 sampel kapal MMSI pada 4 varian ukuran file (8, 16, 32, 64 MiB).
- [x] Hasil & temuan empiris:
  - 100% selesai: 200/200 sukses, 0 failed, durasi 381,8 detik (~6,36 menit).
  - Mekanisme terbukti: Trino membaca ~436–447 MB data di seluruh varian karena predikat `Mmsi` tidak selaras dengan partisi temporal `Date` (*file skipping tidak membantu*).
  - Efek split overhead: Ukuran 8 MiB menghasilkan 76 splits dengan rata-rata latensi terlambat (2.262 ms), sedangkan 64 MiB menghasilkan 53 splits dengan rata-rata latensi tercepat (1.619 ms).
- [x] Deliverables:
  - `scripts/run_q4_robustness.py`.
  - `results/raw/q4_runs.jsonl`.
  - `data/manifests/q4_robustness_report.json`.
- **Status Milestone:** **Q4 Entity Robustness Benchmark LULUS 100% (PASSED)**.

---

### ✅ H14 — Persiapan Minggu 3 & Agregasi Data (P50/P95) (Selesai)
- [x] Buat skrip pemroses data agregasi: `scripts/process_raw_benchmarks.py`.
- [x] Ekstraksi 1.440 measured runs dari `results/raw/runs_frozen.jsonl`.
- [x] Agregasi statistik ke-72 kondisi faktorial unik:
  - Latensi tipikal: $P_{50}$ (median), mean, IQR, dan std deviasi.
  - Latensi beban puncak: $P_{95}$ (tail latency).
  - Telemetri teragregasi: median physical input bytes, median CPU ms, mean completed splits, median peak memory bytes.
- [x] Deliverables:
  - `scripts/process_raw_benchmarks.py`.
  - `results/processed/benchmark_summary_p50_p95.csv`.
  - `data/manifests/week2_completion_report.json`.
- **Status Milestone Minggu 2 (H8–H14):** **MINGGU 2 SELESAI 100% (ALL GATES PASSED)**.

---

## 📝 Catatan Sesi & Keputusan
- **11 September 2026:**
  - Audit workspace menemukan keberadaan clone repo di `D:\DSIC-2604` dan workspace aktif di `D:\Tugas Akhir`.
  - Berkas pelacak progres `src/progres.md` dibuat untuk memandu langkah kerja harian secara bertahap.
  - Prioritas langkah: sinkronisasi workspace/repo, finalisasi H2 (Gate G1), dan persiapan deployment lakehouse (H3).
- **21 September 2026:**
  - Penyelesaian H8: Penanganan 5 issue teknis (resource limits, in-memory REST catalog, register_table procedure, script Python native Windows, dan normalisasi key selektivitas). Seluruh checklist pre-flight lulus 100%.
- **22 September 2026:**
  - Penyelesaian H9: Restorasi catalog berhasil dan eksekusi Main Factorial Benchmark (Eksperimen E3) rampung 100% (1.584 run, 0 failed, telemetri lengkap) dalam waktu 458,5 detik. Data mentah tersimpan di `results/raw/runs.jsonl`.
  - Penyelesaian H10: Audit mutu data mentah & telemetri pada `results/raw/runs.jsonl` menggunakan `scripts/verify_raw_runs.py` berhasil memvalidasi seluruh 6 pilar integritas dengan kelulusan 100% (Gate H10 PASS). Deliverable tersimpan di `data/manifests/gate_h10_telemetry_report.json`.
  - Penyelesaian H11: Evaluasi buffer kueri ulang via `scripts/audit_h11_buffer.py` mengonfirmasi status *Zero-Failure* (0 gagal, 0 hilang), sehingga re-run dinyatakan tidak diperlukan (`CLEARED_NO_RERUN_NEEDED`). Data mentah siap 100% dibekukan pada H12. Deliverable tersimpan di `data/manifests/h11_buffer_clearance_report.json`.
  - Penyelesaian H12: Pembekuan data mentah ke `results/raw/runs_frozen.jsonl` berhasil tuntas (1.584 baris, 1.403.827 bytes) dan disegel dengan sidik jari SHA-256 (`a868d202...`). Data mentah resmi berstatus `FROZEN_AND_VERIFIED`. Deliverable tersimpan di `data/manifests/raw_freeze_manifest.json`.
  - Penyelesaian H13: Eksekusi Out-of-Grid Benchmark Q4 Entity Robustness berhasil tuntas (200 run, 0 failed, durasi 381,8 detik). Temuan empiris mengonfirmasi hipotesis H4 & RQ5: ketika file skipping tidak membantu, file 64 MiB mengungguli 8 MiB akibat lebih rendahnya overhead penjadwalan split (53 vs 76 splits). Deliverable tersimpan di `results/raw/q4_runs.jsonl` dan `data/manifests/q4_robustness_report.json`.
  - Penyelesaian H14: Agregasi 1.440 measured runs menjadi ringkasan statistik P50, P95, IQR, dan telemetri per 72 kondisi berhasil tuntas ke `results/processed/benchmark_summary_p50_p95.csv`. Seluruh gerbang Minggu 2 resmi lulus 100% (ALL GATES PASSED). Repositori siap bertransisi ke Minggu 3 (Analisis, Visualisasi, dan Uji Hipotesis). Deliverable tersimpan di `data/manifests/week2_completion_report.json`.
