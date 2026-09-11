# Log Progres Penelitian DSIC-2604
**Topik:** Interaksi Ukuran Data-File Parquet dan Selektivitas Query pada Lakehouse Bersumber Daya Terbatas: Evaluasi Terkontrol Menggunakan MMDEC  
**Repositori:** [Data-Systems-and-Intelligent-Computing/DSIC-2604](https://github.com/Data-Systems-and-Intelligent-Computing/DSIC-2604)  
**Dataset:** MMDEC (`Dataset_AIS_POS.parquet`) — DOI: [10.5281/zenodo.17491518](https://doi.org/10.5281/zenodo.17491518)  
**Terakhir Diperbarui:** 11 September 2026

---

## 📌 Status Terkini Proyek
- **Status Sinkronisasi Repo:**
  - Repositori remote GitHub: `Data-Systems-and-Intelligent-Computing/DSIC-2604`.
  - Folder lokal: Ditemukan folder `D:\DSIC-2604` (sudah ter-clone dengan git) dan `D:\Tugas Akhir` (workspace aktif di IDE).
  - Berkas H1 telah dibuat di lokal dan dicatat di GitHub.
- **Fase Aktif:** **Minggu 1 (H3 — Deploy Lakehouse & Smoke Test)**.

---

## 🗺️ Roadmap Eksperimen 4 Minggu

| Minggu | Fokus | Eksperimen | Gate Utama | Status |
|---|---|---|---|---|
| **Minggu 1 (H1–H7)** | Freeze, Data, Infrastruktur, Layout, Pilot | E0, E1, E2 | G1–G9 | 🟡 In Progress (H1 ✅, H2 ⏳) |
| **Minggu 2 (H8–H14)** | Main Factorial Benchmark | E3 | Kelengkapan run & telemetry | ⚪ Belum Dimulai |
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
- [x] Catat hasil lengkap ke `rencana-eksperimen-bimbingan/minggu1/README.md`.
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

### ⚪ H6 — Generate Varian Parquet dan Audit
- [ ] Tulis 4 varian ukuran file dari snapshot kanonik yang sama (row-group konstan).
- [ ] Audit separasi IQR dan kesetaraan semantik (Gate **G2, G3, G4**).
- [ ] Catat write cost ke `data/manifests/write_cost_manifest.csv`.

---

### ⚪ H7 — Kalibrasi Selectivity dan Pilot Benchmark
- [ ] Kalibrasi boundary 6 band selectivity (Gate **G5, G6**).
- [ ] Uji pilot protokol benchmark (Gate **G8, G9**).

---

## 📝 Catatan Sesi & Keputusan
- **11 September 2026:**
  - Audit workspace menemukan keberadaan clone repo di `D:\DSIC-2604` dan workspace aktif di `D:\Tugas Akhir`.
  - Berkas pelacak progres `src/progres.md` dibuat untuk memandu langkah kerja harian secara bertahap.
  - Prioritas langkah: sinkronisasi workspace/repo, finalisasi H2 (Gate G1), dan persiapan deployment lakehouse (H3).
