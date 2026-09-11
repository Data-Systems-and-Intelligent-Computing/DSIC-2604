# Catatan Minggu 1

## Rencana Kerja 1 Bulan

28 hari kerja. Setiap hari punya deliverable dan gate yang dapat diperiksa.
Nomor hari bersifat relatif terhadap Hari 1; sesuaikan ke tanggal kalender saat
protokol dibekukan.

### Ringkasan

| Minggu | Fokus | Eksperimen | Gate |
|---|---|---|---|
| 1 (H1–H7) | Freeze, data, infrastruktur, layout, pilot | E0, E1, E2 | G1–G9 |
| 2 (H8–H14) | Main factorial benchmark | E3 | kelengkapan run & telemetry |
| 3 (H15–H21) | Analisis, mekanisme, robustness | E4, E5 | results v1 freeze |
| 4 (H22–H28) | Reproduksi, ekstensi, manuskrip | E5, E6 | quality gate skripsi/artikel |

---

### Minggu 1 — Freeze, Data, Infrastruktur, Layout, Pilot

**H1 — Freeze protokol dan akuisisi data**
- bekukan RQ1–RQ5, hipotesis H1–H5, dan novelty boundary;✅
  
  **🎯 Hasil & Catatan:**
  - **Dokumen Referensi:** Tersimpan dan terkunci di `configs/protocol_freeze.yaml`.
  - **Novelty Boundary:** *Controlled file-size × measured-selectivity interaction study with fixed row-group granularity, predefined crossover criterion, resource constraints, and mechanism attribution*.
  - **Prinsip Utama:** Menolak klaim satu ukuran file "optimal universal". Hasil akhir ditargetkan berupa *conditional decision map*, di mana ketiadaan *crossover* tetap diakui sebagai temuan ilmiah yang sah.
  - **Cakupan RQ & Hipotesis:**
    - **RQ1 & H1 (Interaksi):** Interaksi data-file size vs query selectivity terhadap latency.
    - **RQ2 & H3 (Crossover):** Kestabilan pergeseran ranking antar-ukuran file pada selectivity tertentu.
    - **RQ3 & H4 (Mekanisme):** Atribusi trade-off skipping bytes vs split/scheduling overhead Trino.
    - **RQ4 & H5 (Biaya Write):** Trade-off penulisan dan footprint (file count, layout build time).
    - **RQ5 (Robustness):** Kontrol pengacakan urutan baris (*deterministic shuffled*).


- unduh MMDEC dari DOI `10.5281/zenodo.17491518`, catat tanggal dan lisensi;

  **📦 Hasil & Catatan:**
  - **Dataset Utama:** `Dataset_AIS_POS.parquet` (tersimpan di `D:\Tugas Akhir\Dataset\Dataset_AIS_POS.parquet`).
  - **Sumber Repositori:** Zenodo DOI [`10.5281/zenodo.17491518`](https://doi.org/10.5281/zenodo.17491518).
  - **Artikel Sumber:** *Data in Brief* DOI [`10.1016/j.dib.2026.112629`](https://doi.org/10.1016/j.dib.2026.112629) (Averty et al., 2026).
  - **Lisensi Data:** Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).
  - **Tanggal Akuisisi:** 08 September 2026.


- hitung sha256, isi `data/manifests/source_manifest.csv`.

  **🔐 Hasil & Catatan:**
  - **Ukuran File Fisik:** `450,935,970` bytes (~430.05 MiB).
  - **Algoritma Hash:** SHA-256 (dihitung streaming per blok 64 KB).
  - **Nilai Checksum:** `88998c43f7e152710c3b157cf47c8119cdef05554d2a6d32e980ce36101b5785`.
  - **Status Pencatatan:** Seluruh atribut fisik dan kriptografis berhasil dimasukkan ke file `data/manifests/source_manifest.csv`.


- Deliverable: source manifest terisi.
  - Deliverable: source manifest terisi. ✅

  **📄 Hasil & Bukti Uji:**
  - **Isi Berkas `data/manifests/source_manifest.csv`:**
    ```csv
    dataset_name,role,source_doi,paper_doi,license,download_date,file_path,file_size_bytes,sha256_checksum,expected_row_count,expected_unique_mmsi,verification_status
    Dataset_AIS_POS.parquet,primary_benchmark,10.5281/zenodo.17491518,10.1016/j.dib.2026.112629,CC-BY-NC-4.0,2026-09-08,Dataset/Dataset_AIS_POS.parquet,450935970,88998c43f7e152710c3b157cf47c8119cdef05554d2a6d32e980ce36101b5785,19014229,25130,VERIFIED_H1
    ```
  - **Bukti Eksekusi Test (`pytest -v tests/test_source_contract.py`):**
    ```text
    tests/test_source_contract.py::test_protocol_freeze_exists PASSED        [ 50%]
    tests/test_source_contract.py::test_source_manifest_integrity PASSED     [100%]
    ============================== 2 passed in 0.86s ==============================
    ```


 






  
**H2 — Validasi sumber terhadap artikel**
- jalankan `src/validate_source.py`: row count 19.014.229, MMSI unik 25.130, 14 kolom Tabel 2, tipe `Date` temporal; ✅

  **🎯 Hasil & Catatan:**
  - **Skrip Audit:** Berjalan sukses via `python src/validate_source.py`.
  - **Kesesuaian Baris & MMSI:**
    - Total Baris Terbaca: `19.014.229` baris (100% cocok dengan artikel *Averty et al., 2026*).
    - Kapal Unik (MMSI): `25.130` kapal (100% cocok).
  - **Validasi Skema (Tabel 2 Artikel):**
    - 14 kolom terverifikasi hadir: `Date`, `Mmsi`, `MessageType`, `Latitude`, `Longitude`, `SpeedOverGround`, `CourseOverGroundDegrees`, `TrueHeadingDegrees`, `RateOfTurn`, `NavigationStatus`, `Source`, `PositionAccuracy`, `chunk_folder`, `id_chunk`.
    - Kolom `Date` bertipe temporal (`timestamp[us]`), memenuhi syarat predikat scan tanpa overhead runtime casting.
  - **Status Gate G1:** **PASSED (100%)**.

- EDA distribusi baris per hari (`sql/calibration/rows_per_day.sql` atau DuckDB/PyArrow); ✅

  **📊 Hasil & Catatan:**
  - **Rentang Waktu Observasi:** `2023-06-30 23:58:37` s.d. `2023-09-30 23:58:13` (93 hari kalender).
  - **Karakteristik Distribusi Harian:**
    - Min baris/hari: `183` baris (30 Juni 2023, observasi dimulai 1 menit sebelum tengah malam).
    - Rata-rata baris/hari: `204.454` baris.
    - Median baris/hari: `209.987` baris.
    - Max baris/hari: `245.324` baris.
  - **Implikasi Desain:** Trafik AIS bersifat dinamis fluktuatif (non-seragam). Oleh karena itu, kalibrasi *selectivity band* pada H7 wajib menggunakan *measured selectivity* berbasis predikat `Date` aktual, bukan pembagian waktu linear sederhana.

- **ukur ukuran tabel kanonik** — ini input keputusan grid di H5; ✅

  **📐 Hasil & Catatan:**
  - **Ukuran File Fisik (di disk):** `450.935.970` bytes (~`430,05 MiB`).
  - **Ukuran Data Terkompresi (Column Chunks):** `450.896.019` bytes (~`430,01 MiB`).
  - **Ukuran Data Uncompressed:** `544.528.804` bytes (~`519,30 MiB`).
  - **Rasio Kompresi:** `1,208x`.
  - **Struktur Row Group:** `19` grup (~1 juta baris per grup).
  - **Signifikansi Keputusan Grid (H5):**
    Karena ukuran terkompresi dataset kanonik adalah ~430 MiB, kondisi varian file terbesar 256 MiB hanya akan menghasilkan 1–2 berkas data (< 8 file). Hal ini menjadi alasan empiris kuat mengapa opsi *fallback grid* `8 / 16 / 32 / 64 MiB` disiapkan untuk mempertahankan derajat paralelisasi Trino (*split scheduling*).

- Deliverable: laporan validasi + ukuran tabel. Gate: **G1**. ✅

  **📄 Hasil & Bukti Uji:**
  - **Berkas Bukti Audit:** `data/manifests/gate_g1_validation_report.json`
    ```json
    {
      "gate": "G1",
      "dataset_path": "Dataset/Dataset_AIS_POS.parquet",
      "status": "PASSED",
      "checks": {
        "checksum_sha256": "PASSED",
        "parquet_metadata": "PASSED",
        "semantic_contract": "PASSED"
      },
      "semantic_metrics": {
        "total_rows": 19014229,
        "total_mmsi": 25130,
        "min_date": "2023-06-30 23:58:37",
        "max_date": "2023-09-30 23:58:13",
        "distinct_days": 93,
        "is_passed": true
      }
    }
    ```


**H3 — Deploy lakehouse**
- `docker compose -f infra/docker-compose.yml --env-file .env up -d`;
- verifikasi bucket, katalog Iceberg REST, dan Trino;
- daftarkan tabel kanonik, jalankan `sql/smoke.sql`;
- catat versi persis setiap image ke `data/manifests/environment_snapshot.yaml`.
- Deliverable: smoke test lulus + environment snapshot.

**H4 — Freeze resource dan ukur noise floor**
- bekukan cap CPU/memory di `.env` + `deploy.resources.limits`;
- jalankan satu query ringan 30x untuk mengukur noise floor (CV latency);
- tentukan benchmark window (jam berjalannya run) dan bekukan.
- Deliverable: noise floor terdokumentasi. Gate: **G7**.
- Aturan: perbedaan latency yang lebih kecil dari noise floor tidak boleh
  ditafsirkan di Minggu 3.

**H5 — Baseline layout dan keputusan grid**
- buat canonical snapshot dan layout baseline;
- audit realized file size dan row-group (`src/inspect_parquet.py`);
- **putuskan grid**: utama 32/64/128/256 MiB, atau fallback 8/16/32/64 MiB bila
  kondisi terbesar menghasilkan < 8 file;
- catat keputusan ke `configs/layout.yaml: grid_decision`.
- Deliverable: baseline + keputusan grid beku.

**H6 — Generate seluruh variant dan audit**
- tulis tiga variant sisanya dari canonical snapshot yang sama;
- audit realized file size, separasi IQR antar-kondisi, row-group tetap;
- uji semantic equivalence Q1–Q3 lintas variant;
- catat biaya write ke `data/manifests/write_cost_manifest.csv`.
- Deliverable: layout manifest lengkap. Gate: **G2, G3, G4**.

**H7 — Kalibrasi selectivity dan pilot protokol**
- kalibrasi boundary `Date` untuk 6 band, hitung measured selectivity, bekukan;
- bekukan literal Q1–Q3 dan sampel MMSI untuk Q4;
- pilot: warm-up, protokol cache, randomisasi blok;
- **ukur durasi satu pass penuh** dan bandingkan dengan anggaran H9–H11.
- Deliverable: selectivity manifest + estimasi durasi. Gate: **G5, G6, G8, G9**.

> Main benchmark hanya dimulai jika G1–G9 lulus. Jika salah satu gagal,
> pakai hari buffer H13 sebelum mengorbankan repetisi.

---
