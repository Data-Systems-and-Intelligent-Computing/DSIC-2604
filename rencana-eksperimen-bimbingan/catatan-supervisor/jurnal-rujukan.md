# Ulasan Audit dan Posisi terhadap Penelitian Terdahulu — DSIC-2604

**Judul penelitian yang diaudit:** *Interaksi Ukuran Data-File Parquet dan Selektivitas Query pada Lakehouse Bersumber Daya Terbatas: Evaluasi Terkontrol Menggunakan MMDEC*
**Mahasiswa:** Desman Halawa · **Repositori:** `DSIC-2604/`
**Tanggal ulasan:** 2026-09-27 · **Penyusun:** Supervisor 2
**Commit yang diaudit:** `6ebc23a` (2026-09-12, "update h-5") · **Working tree:** bersih
**Audit sebelumnya:** `supervision/03-dsic-2604/audits/2026-09-12-audit-minggu-1.md` (commit yang sama)

> Dokumen ini adalah artefak supervisi privat (Supervisor 1 / Supervisor 2). Isinya bukan bukti mahasiswa dan tidak boleh disalin ke repositori mahasiswa. Seluruh berkas mahasiswa diperlakukan *read-only*; tidak ada berkas di `DSIC-2604/` yang diubah.

---

## Daftar Isi

1. Ringkasan dari Supervisor 1
2. Cakupan dan Metode
3. Ringkasan Penelitian yang Diaudit
4. Hasil Audit
5. Penelitian Terdahulu: Lima Tahun Terakhir (2021–2026)
6. Penelitian Terdahulu: Enam sampai Sepuluh Tahun Terakhir (2016–2020)
7. Karya Seminal (lebih dari 10 tahun)
8. Perbandingan DSIC-2604 dengan Penelitian Terdahulu
9. Analisis Gap: Apa yang Sudah Dijawab, Apa yang Masih Terbuka, dan Apakah DSIC-2604 Menutupnya
10. Risiko Klaim Novelty dan Rumusan Posisi yang Aman
11. Rekomendasi
12. Keputusan yang Memerlukan Supervisor 1
13. Definition of Done untuk Posisi Literatur
14. Daftar Pustaka Terverifikasi
15. Lampiran: Log Pencarian

---

## 1. Ringkasan dari Supervisor 1

**Status penelitian.** Tidak ada commit baru sejak audit Minggu 1 (HEAD tetap `6ebc23a`, 2026-09-12). Seluruh 17 isu pada register (3 KRITIS, 8 MAYOR, 6 MINOR) masih **TERBUKA**, termasuk dua isu pemblokir: C-01 (grid ukuran file tidak memenuhi Gate G3) dan C-03 (keputusan grid tidak dirambatkan ke konfigurasi dan kode). Pemeriksaan ulang langsung atas berkas konfigurasi mengonfirmasi keduanya masih ada. Belum ada satu pun hasil eksperimen utama (E3), sehingga belum ada klaim empiris yang dapat diuji terhadap literatur.

**Posisi literatur.** Repositori mahasiswa belum memuat satu pun rujukan penelitian terdahulu. Satu-satunya rujukan adalah artikel data MMDEC, dan `paper/manuscript.md` §3 *Related Work* masih kosong. Pada ulasan ini dilakukan pencarian melalui Google Scholar, Crossref, OpenAlex, dan arXiv, lalu 33 karya terdahulu diverifikasi metadatanya (31 `VERIFIED`, 2 `PARTIALLY VERIFIED` karena berstatus preprint).

**Temuan utama dari sisi literatur:**

1. **Karya terdekat adalah preprint Agustus 2026** (Cutura & Prakash, *Smart Compaction*). Penelitian tersebut memvariasikan ukuran file Iceberg lintas tiga orde besaran dan menemukan bahwa compaction dapat **memperlambat agregasi full-scan menjadi 0,45–0,76×** karena jumlah task Spark turun mengikuti jumlah file. Temuan ini adalah bukti eksternal bahwa efek paralelisme dapat mendominasi efek ukuran file. Karena itu isu C-01 (kondisi 64 MiB hanya menghasilkan 6–7 file) bukan kekhawatiran teoretis; isu ini adalah mekanisme yang sudah teramati pada penelitian lain.
2. **Gap yang tampak nyata dan dapat diisi DSIC-2604** adalah studi yang secara sistematis menyilangkan ukuran data-file dengan *measured selectivity*, sambil menahan ukuran row-group tetap, dengan repetisi berpasangan yang cukup dan kriteria crossover yang dibekukan sebelum pengukuran. Pada karya yang diperiksa, studi ukuran file/compaction memakai 1–5 repetisi, tidak menjadikan selektivitas sebagai faktor, dan tidak memisahkan ukuran file dari ukuran row-group.
3. **Temuan desain baru (L-01).** Dengan row-group dibuat tetap, pruning tingkat row-group berlaku identik pada semua varian. Oleh karena itu, keuntungan *data skipping* dari file kecil (mekanisme H2) kemungkinan besar sudah "diserap" oleh pruning row-group, dan perbedaan yang tersisa lebih mungkin berasal dari overhead per file (planning, footer, split). Hal ini tidak membatalkan desain. Justru pertanyaannya menjadi lebih tajam, tetapi H2 dan H4 perlu dirumuskan ulang **sebelum** benchmark agar tidak menjadi perubahan hipotesis *post-hoc*.
4. **Konsep crossover berbasis selektivitas bukan hal baru.** Konsep ini sudah mapan pada literatur *access path selection* (scan vs probe). Yang berpotensi baru adalah penerapannya pada dimensi **granularitas data-file** di lakehouse.

**Kesiapan.** Kesiapan skripsi dan kesiapan publikasi **belum dapat dinilai** karena belum ada hasil. Posisi literatur sekarang sudah dapat dirumuskan, dengan status: *potensi kontribusi teridentifikasi; pencarian 2026-09-27 tidak menemukan studi yang identik, tetapi pencarian ini bukan systematic review sehingga novelty belum dapat dinyatakan.*

**Keputusan yang menunggu:** D-01, D-02, D-03 (dari audit Minggu 1, belum diputuskan) serta D-04 dan D-05 yang baru (lihat §12).

---

## 2. Cakupan dan Metode

### 2.1 Audit repositori

| Aspek | Keterangan |
|---|---|
| Jenis | Audit progres + audit posisi literatur |
| Dasar | Audit Minggu 1 (2026-09-12), register isu, dan inspeksi ulang berkas pada `6ebc23a` |
| Perubahan sejak audit terakhir | Tidak ada (`git log` dan `git status` tidak berubah) |
| Berkas yang diperiksa ulang | `README.md`, `configs/{protocol_freeze,layout,crossover,benchmark,selectivity}.yaml`, `sql/queries/Q1–Q4`, `paper/manuscript.md`, `refs/README.md` |
| Batasan | Tidak ada eksekusi Docker/Trino; dataset tidak tersedia di mesin auditor |

### 2.2 Pencarian penelitian terdahulu

Pencarian dilakukan pada **2026-09-27** dengan prioritas publikasi 5 tahun terakhir (2021–2026) dan 10 tahun terakhir (2016–2020). Karya di luar rentang tersebut hanya dimasukkan bila bersifat seminal dan dikutip langsung oleh karya dalam rentang.

| Sumber | Peran |
|---|---|
| Google Scholar | titik awal pencarian (kueri dicatat pada Lampiran §15) |
| Crossref (`api.crossref.org`) | verifikasi judul, penulis, tahun, venue, DOI |
| OpenAlex | abstrak dan tautan open access |
| arXiv API + PDF | metadata dan full text preprint |
| Halaman resmi (USENIX, CIDR, VLDB) | verifikasi karya tanpa DOI |

**Status verifikasi.** `VERIFIED` berarti metadata cocok pada DOI atau halaman resmi. `PARTIALLY VERIFIED` berarti karya ditemukan, tetapi status venue atau sebagian metadata belum terkonfirmasi. **Bukti yang diperiksa** dicatat per karya: *full text*, *abstrak*, atau *metadata saja*. Klaim tentang isi paper hanya diambil dari bagian yang benar-benar dibaca.

Jumlah sitasi tidak dijadikan dasar pemilihan. Angka sitasi yang dicantumkan adalah hitungan Crossref pada 2026-09-27 dan akan berubah seiring waktu.

---

## 3. Ringkasan Penelitian yang Diaudit

| Unsur | Isi (sumber: `configs/protocol_freeze.yaml`, `README.md`) |
|---|---|
| Bidang | Data systems |
| Masalah | Pengaruh ukuran data-file Parquet terhadap latency query analitik bergantung pada selektivitas query; ukuran "optimal universal" dianggap tidak ada |
| RQ1 | Bagaimana ukuran data-file berinteraksi dengan selektivitas terhadap latency, bila row-group, row order, partitioning, compression, engine, dan hardware ditahan tetap |
| RQ2 | Apakah peringkat relatif antarukuran berubah (crossover) secara stabil |
| RQ3 | Mekanisme: physical input bytes, processed rows/bytes, split, CPU, memori |
| RQ4 | Biaya write/compaction per regime ukuran file |
| RQ5 | Robustness: row-order control atau tabel MMDEC kedua (bukan syarat skripsi) |
| Faktor A | Ukuran data-file: grid utama 32/64/128/256 MiB; grid fallback 8/16/32/64 MiB (dipilih H5) |
| Faktor B | Measured selectivity 6 band (0,01 %–50 %) pada predikat rentang `Date` |
| Kontrol | Row-group tetap, *date-clustered*, unpartitioned, Snappy, Trino, concurrency 1 |
| Query | Q1 `COUNT(*)`, Q2 `AVG/MAX(SpeedOverGround)`, Q3 `GROUP BY MessageType`, Q4 entity (`Mmsi IN`) |
| Stack | MinIO + Iceberg REST catalog + Trino, Spark untuk menulis layout; Docker Compose, host target 8 vCPU/16 GB |
| Dataset | MMDEC `Dataset_AIS_POS.parquet`: 19.014.229 baris, 25.130 MMSI (Averty et al., 2026) |
| Statistik | 20 repetisi terukur per kondisi, randomisasi blok, paired bootstrap 95 % CI, Holm, model interaksi log-latency |
| Klaim novelty | "controlled file-size × measured-selectivity interaction study dengan fixed row-group granularity, predefined crossover criterion, resource constraints, dan mechanism attribution" |
| Klaim negatif | Bukan pencarian ukuran optimal universal; bukan benchmark domain maritim; bukan perbandingan MinIO/Iceberg/Trino |

Rumusan klaim negatif ini sudah tepat dan sejalan dengan literatur (lihat §9). Mahasiswa secara eksplisit menolak menjadikan domain maritim atau pilihan perangkat lunak sebagai novelty.

---

## 4. Hasil Audit

### 4.1 Status gate dan isu (tidak berubah sejak 2026-09-12)

| Gate | Putusan auditor | Isu terkait |
|---|---|---|
| G1 Data | Lulus dengan catatan | M-04, M-05, M-07, M-08 |
| G2 Semantic equivalence | Belum diuji | N-01 |
| G3 Separasi & kelayakan grid | **Tidak lulus** | **C-01**, C-03, N-02, N-03 |
| G4 Kontrol row-group | Belum diuji | N-04 |
| G5 Selectivity | Belum dikerjakan | M-05 |
| G6 Observability | Belum diuji | — |
| G7 Resource freeze | **Tidak lulus** | **C-02**, M-01, M-02 |
| G8 Baseline | Belum dikerjakan | C-03 |
| G9 Claim freeze | Sebagian | C-03, M-06 |

Verifikasi ulang pada ulasan ini:

- `configs/layout.yaml` masih memuat `canonical_table_size_mib: 450.05` (nilai MB yang diberi label MiB; ukuran sebenarnya 430,05 MiB). **C-01 tetap TERBUKA.**
- `configs/benchmark.yaml` masih `file_size_mib: [32, 64, 128, 256]` dan metrik `latency_ratio_vs_128mib`; `configs/crossover.yaml` masih `baseline_file_size_mib: 128`. **C-03 tetap TERBUKA.**
- `configs/selectivity.yaml` masih membekukan 92 hari mulai 2023-07-01. **M-05 tetap TERBUKA.**

Rincian bukti setiap isu tidak diulang di sini dan dapat dilihat pada `supervision/03-dsic-2604/audits/2026-09-12-audit-minggu-1.md` serta `issue-register.md`.

### 4.2 Temuan baru dari pembacaan literatur

Temuan berikut muncul ketika desain DSIC-2604 dibandingkan dengan penelitian terdahulu. Temuan ini belum tercatat pada register isu.

#### L-01 — Row-group yang ditahan tetap berpotensi menetralkan mekanisme H2

**Severity: MAYOR** · Berdampak pada H2, H4, RQ3 · Kategori: validitas penelitian

*Yang ada.* Desain menahan target row-group tetap pada semua varian ukuran file (`configs/layout.yaml`, invarian `same_row_group_target`). H2 menyatakan bahwa file lebih kecil "dapat mengurangi latency atau physical input", dan H4 menjelaskan mekanismenya sebagai *data skipping/physical-input reduction vs file-open/split/scheduling overhead*.

*Yang diketahui dari literatur.* Parquet menyimpan zone map (min/max) pada tingkat file dan tingkat row-group (Zeng et al., 2023, §3.5, full text diperiksa). Pada data yang terurut menurut `Date`, predikat rentang `Date` dapat dipangkas pada kedua tingkat tersebut.

*Inferensi.* Karena ukuran row-group sama pada semua varian, granularitas pruning terhalus juga sama. Varian 8 MiB memangkas file di tahap planning, sedangkan varian 64 MiB membuka file lalu memangkas row-group di dalamnya. Selisih *physical input bytes* antarvarian diduga kecil, yaitu terbatas pada pembacaan footer dan row-group yang terpotong di tepi rentang. Perbedaan latency yang tersisa lebih mungkin berasal dari overhead per file dan jumlah split. README mahasiswa sendiri sudah mengantisipasi kemungkinan ini ("bisa lemah jika row-group pruning lebih dominan daripada file-level effect").

*Yang belum pasti.* Perilaku pruning row-group oleh reader Parquet Trino pada versi yang dibekukan **belum diverifikasi** di repositori ini. Inferensi di atas harus diuji, bukan diasumsikan.

*Konsekuensi.* Bila inferensi ini benar, H2 (pengurangan physical input) hampir pasti ditolak. Penolakan itu sah, tetapi akan tampak seperti "hasil negatif" bila hipotesis tidak dirumuskan ulang. Sebaliknya, desain ini sebenarnya menjawab pertanyaan yang lebih tajam dan lebih menarik bagi reviewer: *apakah granularitas file masih berpengaruh ketika granularitas row-group sudah dikendalikan?*

*Rekomendasi:* §11, R-1. *Perlu keputusan Supervisor 1:* D-04.

#### L-02 — Q1 (`COUNT(*)`) kemungkinan didominasi overhead metadata

**Severity: MAYOR** · Berdampak pada RQ1–RQ3, validitas konstruk

Cutura & Prakash (2026, full text diperiksa, §III-H) melaporkan bahwa `COUNT(*)` full-scan paling diuntungkan compaction (median 1,19×) dan menyimpulkan bahwa kueri jenis ini didominasi overhead metadata (listing file, pembacaan footer Parquet). Q1 DSIC-2604 adalah `COUNT(*)` dengan predikat `Date`. Hasil Q1 diduga lebih mengukur overhead per file daripada biaya scan. Hal itu bukan kesalahan, tetapi berarti Q1 dan Q2/Q3 mengukur mekanisme yang berbeda. Syarat crossover di `configs/crossover.yaml` (`require_replicated_direction_across_main_query_family: true`) bisa gagal justru karena perbedaan mekanisme ini, bukan karena tidak adanya interaksi.

Apakah Trino menjawab `COUNT(*)` berpredikat dari statistik metadata tanpa membaca data **belum diverifikasi**. Hal ini perlu diperiksa dengan `EXPLAIN ANALYZE` pada satu band sebelum E3.

#### L-03 — Nilai 7,83 % tidak boleh dilegitimasi dengan literatur variansi lakehouse

**Severity: MINOR (pencegahan)** · Memperkuat C-02

Nurdin et al. (2026, full text diperiksa) melaporkan median CV 4–9 % untuk kueri Trino/Iceberg di cloud publik dengan 5 repetisi. Angka ini tampak "sejalan" dengan noise floor 7,83 % mahasiswa, sehingga ada risiko mahasiswa mengutipnya sebagai pembenaran. Keduanya tidak sebanding. Nurdin et al. mengukur kueri benchmark nyata pada klaster terdistribusi dengan co-tenant di cloud, sedangkan angka mahasiswa berasal dari `SELECT 1` pada host tunggal dan didominasi artefak polling 50 ms (C-02). Literatur variansi performa (Maricq et al., 2018; Uta et al., 2020; Papadopoulos et al., 2021) justru mendukung perbaikan C-02: noise floor harus diukur dengan instrumen dan workload yang sama dengan pengukuran efek.

#### L-04 — Panduan ukuran objek dari S3 tidak dapat dipindahkan langsung ke MinIO lokal

**Severity: MINOR** · Validitas eksternal

Durner et al. (2023, full text diperiksa) menemukan bahwa pada AWS S3 ukuran request sekitar 8–16 MiB memberi keseimbangan biaya-throughput, karena latency round-trip mendominasi request kecil. Grid fallback DSIC-2604 (8–64 MiB) berada di sekitar rentang ini, sehingga mahasiswa mungkin tergoda mengaitkan hasil dengan temuan tersebut. MinIO yang berjalan pada host yang sama memiliki latency per request jauh lebih rendah dan tidak diukur pada Durner et al. Penalti file kecil pada DSIC-2604 diduga lebih rendah daripada di object store cloud. Klaim harus dibatasi pada object store lokal, sesuai batas yang sudah tertulis di README §External Validity.

#### L-05 — Tidak ada related work; manuskrip §3 kosong

**Severity: MAYOR untuk publikasi, MINOR untuk skripsi pada tahap ini**

`refs/README.md` hanya memuat artikel data MMDEC. README §Quality Gate Artikel mensyaratkan "final literature verification selesai" dan melarang klaim "first study" tanpa bukti. Ulasan ini menyediakan peta kandidat (§5–§7), tetapi penulisan related work tetap merupakan pekerjaan mahasiswa.

### 4.3 Status klaim terhadap bukti

| Klaim | Status | Dasar |
|---|---|---|
| Efek ukuran file bergantung pada selektivitas (H1) | **NOT TESTED** | Belum ada E3 |
| File kecil mengurangi physical input pada selektivitas rendah (H2) | **NOT TESTED**; berisiko ditolak secara struktural | L-01 |
| Crossover ada dan stabil (H3) | **NOT TESTED** | Kriteria masih merujuk baseline 128 MiB yang tidak akan ada (C-03) |
| Mekanisme skipping vs overhead (H4) | **NOT TESTED** | Perlu metrik file terpangkas vs terbaca |
| File kecil meningkatkan biaya write (H5) | **NOT TESTED** | Sejalan arah dengan literatur compaction (§5), tetapi belum diukur |
| "Controlled interaction study … belum ada sebelumnya" | **INSUFFICIENT EVIDENCE** | Pencarian terbatas, bukan systematic review (§10) |

---

## 5. Penelitian Terdahulu: Lima Tahun Terakhir (2021–2026)

Karya dikelompokkan menjadi lima kluster: (A) ukuran file, compaction, dan table format lakehouse; (B) format kolumnar dan akses object store; (C) data skipping dan layout; (D) metodologi pengukuran; (E) konteks lakehouse dan domain. Tanda ★ menandai karya yang paling dekat dengan DSIC-2604.

### Kluster A — Ukuran file, compaction, dan table format lakehouse

#### A1 ★ Smart Compaction: Predicting Compaction Utility from Lakehouse Table Metadata

| Field | Isi |
|---|---|
| Penulis | Jannic Cutura, Subash Prakash |
| Tahun / Venue / Jenis | 2026 · arXiv · preprint |
| Identifier | arXiv:2608.08639 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22Smart+Compaction%3A+Predicting+Compaction+Utility+from+Lakehouse+Table+Metadata%22> |
| Sumber resmi | <https://arxiv.org/abs/2608.08639> |
| Masalah & metode | Kapan compaction bin-packing Iceberg bermanfaat; 2.376 tabel Iceberg simulasi dengan ukuran file 8 KB–128 MB; 17 fitur metadata manifest; XGBoost |
| Dataset / konteks | Tabel sintetis (payload UUID) dan 96 tabel TPC-H; Spark-local |
| Temuan utama | Keputusan compaction dapat dipisahkan dengan ambang `max_files_per_partition > 4`. Pada benchmark kueri, `COUNT(*)` full-scan dipercepat (median 1,19×), sedangkan agregasi full-scan melambat (0,45–0,76×) karena jumlah task Spark proporsional terhadap jumlah file. Median keseluruhan 0,97×. Tiap kueri: 1 warm-up, 3 run terukur, dilaporkan median |
| Relevansi | Karya terdekat: memvariasikan ukuran/jumlah file Iceberg dan mengukur dampaknya pada latency |
| Persamaan | Iceberg, Parquet, ukuran file sebagai variabel, perhatian pada paralelisme dan metadata overhead |
| Perbedaan | Tidak ada sumbu selektivitas yang terkalibrasi; row-group tidak dikendalikan; engine Spark-local, bukan Trino; 3 repetisi tanpa CI pada benchmark kueri; data sintetis/TPC-H |
| Gap yang tersisa | Interaksi ukuran file × selektivitas dengan row-group tetap dan repetisi berpasangan yang cukup belum diuji |
| Bukti diperiksa | Full text (abstrak, §II-B, §III-H, §III-I, §IV) |
| Sumber verifikasi | arXiv API + PDF |
| Status | **PARTIALLY VERIFIED** (preprint, belum ada versi terbit yang terkonfirmasi) |

#### A2 ★ LST-Bench: Benchmarking Log-Structured Tables in the Cloud

| Field | Isi |
|---|---|
| Penulis | Jesús Camacho-Rodríguez, Ashvin Agrawal, Anja Gruenheid, Ashit Gosalia, Cristian Petculescu, Josep Aguilar-Saborit, Avrilia Floratou, Carlo Curino |
| Tahun / Venue / Jenis | 2024 · Proceedings of the ACM on Management of Data (SIGMOD 2024) · journal |
| DOI | 10.1145/3639314 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22LST-Bench%3A+Benchmarking+Log-Structured+Tables+in+the+Cloud%22> |
| Sumber resmi | <https://doi.org/10.1145/3639314> · arXiv:2305.01120 |
| Masalah & metode | Benchmark khusus log-structured tables (Delta, Iceberg, Hudi) yang memperhitungkan evolusi tabel dari waktu ke waktu; dievaluasi dengan Spark dan Trino |
| Temuan utama | Abstrak: benchmark konvensional tidak memadai untuk mengukur dampak pilihan desain dan optimasi pada lapisan storage. Menurut Cutura & Prakash (2026), LST-Bench mengamati bahwa efek compaction bergantung pada workload (sumber sekunder) |
| Relevansi | Menyediakan kerangka dan metrik untuk degradasi dan maintenance tabel; relevan untuk RQ4 |
| Perbedaan | Fokus pada evolusi tabel dan perbandingan format, bukan interaksi ukuran file × selektivitas yang dikendalikan |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### A3 AutoComp: Automated Data Compaction for Log-Structured Tables in Data Lakes

| Field | Isi |
|---|---|
| Penulis | Anja Gruenheid, Jesús Camacho-Rodríguez, Carlo Curino, Raghu Ramakrishnan, Stanislav Pak, Sumedh Sakdeo, Lenisha Gandhi, Sandeep K. Singhal |
| Tahun / Venue / Jenis | 2025 · Companion of SIGMOD 2025 · conference (industrial) |
| DOI | 10.1145/3722212.3724430 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22AutoComp%3A+Automated+Data+Compaction+for+Log-Structured+Tables+in+Data+Lakes%22> |
| Masalah & metode | Proliferasi file kecil menurunkan performa kueri; framework compaction otomatis berdasarkan pengalaman deployment di LinkedIn |
| Temuan utama | Abstrak: perbaikan pada pengurangan jumlah file dan performa kueri pada benchmark sintetis dan produksi |
| Relevansi | Memberi dasar praktis bahwa "file kecil merugikan" adalah masalah operasional nyata; relevan untuk H5/RQ4 |
| Perbedaan | Sistem produksi skala besar; tidak mengukur kapan file kecil justru menguntungkan |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### A4 An Empirical Study of Open Lakehouse Table Formats on Object Storage

| Field | Isi |
|---|---|
| Penulis | Vipul Shyam Javeri |
| Tahun / Venue / Jenis | 2026 · IEEE SoutheastCon 2026 · conference |
| DOI | 10.1109/southeastcon63549.2026.11475985 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22An+Empirical+Study+of+Open+Lakehouse+Table+Formats+on+Object+Storage%22> |
| Masalah & metode | Evaluasi Iceberg, Hudi, Delta di Spark dengan backend MinIO bersama; latency write, kueri analitik, dan upsert; jumlah data file dan metadata file dari object listing |
| Relevansi | Stack paling mirip (MinIO, Iceberg) dan sama-sama mencatat jumlah file |
| Perbedaan | Membandingkan format, bukan ukuran file; selektivitas tidak dikendalikan |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### A5 Analyzing and Comparing Lakehouse Storage Systems

| Field | Isi |
|---|---|
| Penulis | Paras Jain, Peter Kraft, Conor Power, Tathagata Das, Ion Stoica, Matei Zaharia |
| Tahun / Venue / Jenis | 2023 · CIDR 2023 · conference |
| Identifier | Tidak ada DOI; <https://www.cidrdb.org/cidr2023/papers/p92-jain.pdf> |
| Google Scholar | <https://scholar.google.com/scholar?q=%22Analyzing+and+Comparing+Lakehouse+Storage+Systems%22> |
| Masalah & metode | Analisis desain Delta, Hudi, Iceberg; LHBench berbasis TPC-DS |
| Temuan utama | Halaman 1: sistem lakehouse harus melayani workload skala besar dan kueri interaktif pada tabel lebih kecil di atas object store berlatensi tinggi. Isi teks menyinggung ukuran file dan strategi compaction sebagai sumbu perbedaan desain |
| Relevansi | Rujukan standar untuk trade-off desain lakehouse |
| Bukti diperiksa | Abstrak dan sebagian full text (pencarian kata kunci) |
| Status | **VERIFIED** (PDF resmi CIDR) |

#### A6 LakeHelm: Zero-Shot Lakehouse Advisor for Joint Engine-Format Selection and Configuration

| Field | Isi |
|---|---|
| Penulis | Zhongwei Xu, Siyuan Dong, Haotian Gong, Donna Pham, Lin Ma |
| Tahun / Venue / Jenis | 2026 · Proceedings of the VLDB Endowment 19 · journal |
| DOI | 10.14778/3811243.3811250 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22LakeHelm%22+lakehouse+advisor> |
| Temuan utama | Abstrak: pilihan engine, format, dan konfigurasinya berinteraksi secara kompleks; rata-rata 1,35× speedup terhadap konfigurasi terbaik tetap |
| Relevansi | Mendukung premis DSIC-2604 bahwa parameter lakehouse saling berinteraksi sehingga tidak ada satu konfigurasi optimal universal |
| Perbedaan | Pendekatan learned advisor pada benchmark standar; bukan studi mekanisme terkontrol |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

### Kluster B — Format kolumnar dan akses object store

#### B1 ★ An Empirical Evaluation of Columnar Storage Formats

| Field | Isi |
|---|---|
| Penulis | Xinyu Zeng, Yulong Hui, Jiahong Shen, Andrew Pavlo, Wes McKinney, Huanchen Zhang |
| Tahun / Venue / Jenis | 2023 · Proceedings of the VLDB Endowment 17(2) · journal |
| DOI | 10.14778/3626292.3626298 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22An+Empirical+Evaluation+of+Columnar+Storage+Formats%22> |
| Sumber resmi | <https://doi.org/10.14778/3626292.3626298> · arXiv:2304.05028 |
| Masalah & metode | Kajian ulang internal Parquet dan ORC; benchmark yang menstres format pada berbagai konfigurasi workload, termasuk selektivitas predikat |
| Temuan utama | Merekomendasikan dictionary encoding sebagai default dan zone map yang lebih halus. Zone map Parquet berada pada tingkat file dan row-group; zone map hanya efektif bila nilai terklaster. Sistem mengatur ukuran row-group untuk menyeimbangkan rasio kompresi, overhead metadata, dan paralelisme scan |
| Relevansi | Dasar teoretis untuk L-01 dan untuk bagian Background manuskrip (§2.1, §2.3) |
| Perbedaan | Unit analisis adalah format, bukan ukuran data-file dalam tabel lakehouse |
| Bukti diperiksa | Full text (arXiv) |
| Status | **VERIFIED** (Crossref) |

#### B2 A Deep Dive into Common Open Formats for Analytical DBMSs

| Field | Isi |
|---|---|
| Penulis | Chunwei Liu, Anna Pavlenko, Matteo Interlandi, Brandon Haynes |
| Tahun / Venue / Jenis | 2023 · PVLDB 16(11) · journal |
| DOI | 10.14778/3611479.3611507 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22A+Deep+Dive+into+Common+Open+Formats+for+Analytical+DBMSs%22> |
| Temuan utama | Abstrak: Arrow, Parquet, dan ORC masing-masing memiliki trade-off untuk kueri OLAP |
| Relevansi | Konteks Background; bukan pembanding langsung |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### B3 Exploiting Cloud Object Storage for High-Performance Analytics

| Field | Isi |
|---|---|
| Penulis | Dominik Durner, Viktor Leis, Thomas Neumann |
| Tahun / Venue / Jenis | 2023 · PVLDB 16(11) · journal |
| DOI | 10.14778/3611479.3611486 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22Exploiting+Cloud+Object+Storage+for+High-Performance+Analytics%22> |
| Sumber resmi | <https://www.vldb.org/pvldb/vol16/p2769-durner.pdf> |
| Masalah & metode | Studi mendalam retrieval dari object store cloud untuk pemrosesan kueri; AnyBlob download manager |
| Temuan utama | Ukuran request kecil dibatasi latency round-trip; dari 8 ke 16 MiB masih ada perbaikan kecil, sedangkan di atas itu durasi naik sebanding dengan ukuran. Rentang request yang optimal biaya-throughput didefinisikan |
| Relevansi | Menjelaskan mengapa objek kecil mahal pada object store; dasar L-04 |
| Perbedaan | AWS S3 cloud, bukan MinIO lokal; unit analisis request, bukan data-file tabel |
| Bukti diperiksa | Full text (bagian retrieval) |
| Status | **VERIFIED** (Crossref + PDF VLDB) |

#### B4 Selection Pushdown in Column Stores using Bit Manipulation Instructions

| Field | Isi |
|---|---|
| Penulis | Yinan Li, Jianan Lu, Badrish Chandramouli |
| Tahun / Venue / Jenis | 2023 · PACMMOD (SIGMOD 2023) · journal |
| DOI | 10.1145/3589323 |
| Temuan utama | Abstrak: selection pushdown pada Parquet mempercepat scan kueri representatif hingga satu orde besaran |
| Relevansi | Menunjukkan bahwa biaya kueri selektif pada Parquet juga ditentukan oleh decoding, bukan hanya I/O; relevan sebagai ancaman validitas mekanisme (RQ3) |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### B5 Active Data Lakes: Regaining Physical Data Independence Without Losing Interoperability

| Field | Isi |
|---|---|
| Penulis | Pascal Ginter, Viktor Leis |
| Tahun / Venue / Jenis | 2026 · PVLDB · journal |
| DOI | 10.14778/3797919.3797941 |
| Temuan utama | Abstrak: integrasi erat engine dengan Parquet mengorbankan physical data independence dan menghambat adopsi optimasi pada file format, access path, dan media penyimpanan |
| Relevansi | Konteks mutakhir: keputusan layout fisik (termasuk ukuran file) masih dibebankan kepada pengguna data lake |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

### Kluster C — Data skipping dan layout

#### C1 Instance-Optimized Data Layouts for Cloud Analytics Workloads

| Field | Isi |
|---|---|
| Penulis | Jialin Ding, Umar Farooq Minhas, Badrish Chandramouli, Chi Wang, Yinan Li, Ying Li, Donald Kossmann, Johannes Gehrke |
| Tahun / Venue / Jenis | 2021 · SIGMOD 2021 · conference |
| DOI | 10.1145/3448016.3457270 |
| Temuan utama | Abstrak: efektivitas block skipping dengan zone map bergantung pada bagaimana record ditempatkan ke blok; I/O dari cloud storage sering dominan |
| Relevansi | Mendukung desain *date-clustered*: efek ukuran blok hanya bermakna bila penempatan record selaras dengan predikat |
| Perbedaan | Mengoptimalkan penempatan record, bukan ukuran blok |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### C2 Pando: Enhanced Data Skipping with Logical Data Partitioning

| Field | Isi |
|---|---|
| Penulis | Sivaprasad Sudhir, Wenbo Tao, Nikolay Laptev, Cyrille Habis, Michael Cafarella, Samuel Madden |
| Tahun / Venue / Jenis | 2023 · PVLDB 16(9) · journal |
| DOI | 10.14778/3598581.3598601 |
| Temuan utama | Abstrak: hingga 2,8× pengurangan blok yang dipindai dan 2,3× speedup end-to-end |
| Relevansi | Menunjukkan bahwa "jumlah blok yang diakses" adalah metrik mekanisme yang lazim; DSIC-2604 dapat memakai padanannya (file terpangkas vs terbaca) |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### C3 Dynamic Data Layout Optimization with Worst-case Guarantees (OReO)

| Field | Isi |
|---|---|
| Penulis | Kexin Rong, Paul Liu, Sarah Ashok Sonje, Moses Charikar |
| Tahun / Venue / Jenis | 2024 · ICDE 2024 · conference |
| DOI | 10.1109/icde60146.2024.00327 · arXiv:2405.04984 |
| Temuan utama | Abstrak: reorganisasi online yang menyeimbangkan manfaat kueri dan biaya reorganisasi; hingga 32 % perbaikan waktu kueri + reorganisasi |
| Relevansi | Kerangka konseptual untuk RQ4: manfaat layout harus dinilai bersama biaya menulis ulang |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref + arXiv) |

#### C4 Ameliorating Data Compression and Query Performance through Cracked Parquet

| Field | Isi |
|---|---|
| Penulis | Patrick Hansert, Sebastian Michel |
| Tahun / Venue / Jenis | 2022 · BiDEDE Workshop @ SIGMOD 2022 · workshop |
| DOI | 10.1145/3530050.3532923 |
| Temuan utama | Abstrak: partitioning pada data nested Parquet memberi rasio kompresi 1,37 dan runtime kueri 1,22× lebih cepat |
| Relevansi | Contoh studi layout Parquet skala kecil di venue workshop; relevan sebagai pembanding skala kontribusi |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

### Kluster D — Metodologi pengukuran dan sumber daya

#### D1 ★ Predicting Lakehouse Performance in Clouds: An Empirical Exploration of Query Runtime Variance

| Field | Isi |
|---|---|
| Penulis | James Nurdin, Wei Liu, Richard Mccreadie, Lauritz Thamsen |
| Tahun / Venue / Jenis | 2026 · arXiv; menurut komentar arXiv akan terbit di IEEE CLOUD 2026 · preprint |
| Identifier | arXiv:2606.03464 |
| Google Scholar | <https://scholar.google.com/scholar?q=%22Predicting+Lakehouse+Performance+in+Clouds%22> |
| Masalah & metode | Kuantifikasi variansi runtime kueri lakehouse Trino/Iceberg pada tiga cloud publik dan satu cloud privat; 5 repetisi workload |
| Temuan utama | Eksekusi berulang kueri yang sama dapat berbeda hampir dua kali lipat; median CV 4–9 % dan CV P99 20–50 % di cloud publik; faktor variansi mencakup data locality, co-tenant load, dan caching |
| Relevansi | Satu-satunya karya yang ditemukan tentang variansi pada stack yang sama (Trino + Iceberg); relevan untuk C-02 dan L-03 |
| Perbedaan | Klaster terdistribusi di cloud; tujuan prediksi performa, bukan efek layout |
| Bukti diperiksa | Full text (bagian metodologi dan hasil variansi) |
| Status | **PARTIALLY VERIFIED** (preprint; status terbit belum dikonfirmasi) |

#### D2 Methodological Principles for Reproducible Performance Evaluation in Cloud Computing

| Field | Isi |
|---|---|
| Penulis | Alessandro Vittorio Papadopoulos, Laurens Versluis, André Bauer, Nikolas Herbst, Jóakim von Kistowski, Ahmed Ali-Eldin, Cristina L. Abad, José Nelson Amaral |
| Tahun / Venue / Jenis | 2021 · IEEE Transactions on Software Engineering · journal |
| DOI | 10.1109/TSE.2019.2927908 |
| Temuan utama | Abstrak: delapan prinsip metodologis; tinjauan literatur 2012–2017 menunjukkan hanya sedikit studi yang mengikutinya |
| Relevansi | Rujukan untuk membenarkan protokol repetisi, randomisasi, dan pelaporan DSIC-2604 |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### D3 Modern Alternatives to Hive: A Systematic Review and Single-Node Benchmark of SQL-on-Hadoop and Lakehouse Engines

| Field | Isi |
|---|---|
| Penulis | Szoke Mark-Andor |
| Tahun / Venue / Jenis | 2026 · Information Systems · journal |
| DOI | 10.1016/j.is.2025.102635 |
| Temuan utama | Abstrak: 11 engine pada satu node (4 core, 8 thread), TPC-H SF 1 dan SF 10; engine native/vectorized jauh lebih cepat daripada stack JVM (Spark SQL, Trino) pada satu node |
| Relevansi | Preseden untuk evaluasi lakehouse "resource-constrained" pada satu node; juga peringatan bahwa Trino pada satu node memiliki overhead JVM yang ikut memengaruhi skala efek |
| Perbedaan | Membandingkan engine, bukan layout |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### D4 Towards Cost-Optimal Query Processing in the Cloud

| Field | Isi |
|---|---|
| Penulis | Viktor Leis, Maximilian Kuschewski |
| Tahun / Venue / Jenis | 2021 · PVLDB · journal |
| DOI | 10.14778/3461535.3461549 |
| Temuan utama | Abstrak: performa dan biaya dapat berbeda beberapa orde besaran tergantung konfigurasi hardware |
| Relevansi | Mendukung argumen bahwa hasil layout harus dinyatakan bersyarat pada anggaran sumber daya |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

### Kluster E — Konteks lakehouse dan domain

#### E1 Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics

| Field | Isi |
|---|---|
| Penulis | Michael Armbrust, Ali Ghodsi, Reynold Xin, Matei Zaharia |
| Tahun / Venue / Jenis | 2021 · CIDR 2021 · conference |
| Identifier | Tidak ada DOI; <https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf> |
| Relevansi | Definisi arsitektur lakehouse berbasis format terbuka seperti Parquet; rujukan pengantar |
| Bukti diperiksa | Abstrak (PDF resmi) |
| Status | **VERIFIED** (PDF resmi CIDR) |

#### E2 The Lakehouse: State of the Art on Concepts and Technologies

| Field | Isi |
|---|---|
| Penulis | Jan Schneider, Christoph Gröger, Arnold Lutsch, Holger Schwarz, Bernhard Mitschang |
| Tahun / Venue / Jenis | 2024 · SN Computer Science · review |
| DOI | 10.1007/s42979-024-02737-0 |
| Relevansi | Survei konsep dan teknologi lakehouse; rujukan untuk definisi |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### E3 Design of Vessel Data Lakehouse with Big Data and AI Analysis Technology for Vessel Monitoring System

| Field | Isi |
|---|---|
| Penulis | Sun Park, Chan-Su Yang, JongWon Kim |
| Tahun / Venue / Jenis | 2023 · Electronics (MDPI) · journal |
| DOI | 10.3390/electronics12081943 |
| Relevansi | Bukti bahwa lakehouse untuk data kapal sudah diusulkan sebelumnya. Hal ini mendukung keputusan mahasiswa untuk **tidak** menjadikan domain maritim sebagai novelty |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

---

## 6. Penelitian Terdahulu: Enam sampai Sepuluh Tahun Terakhir (2016–2020)

#### F1 Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores

| Field | Isi |
|---|---|
| Penulis | Michael Armbrust, Tathagata Das, Liwen Sun, Burak Yavuz, Shixiong Zhu, Mukul Murthy, Joseph Torres, Herman van Hovell, dkk. |
| Tahun / Venue / Jenis | 2020 · PVLDB 13(12) · journal |
| DOI | 10.14778/3415478.3415560 |
| Temuan utama | Abstrak: object store berbasis key-value membuat operasi metadata seperti listing mahal; Delta Lake menyediakan optimasi layout data otomatis |
| Relevansi | Dasar mengapa jumlah file dan metadata menjadi biaya pada lakehouse |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### F2 Qd-tree: Learning Data Layouts for Big Data Analytics

| Field | Isi |
|---|---|
| Penulis | Zongheng Yang, Badrish Chandramouli, Chi Wang, Johannes Gehrke, Yinan Li, Umar Farooq Minhas, Per-Åke Larson, Donald Kossmann |
| Tahun / Venue / Jenis | 2020 · SIGMOD 2020 · conference |
| DOI | 10.1145/3318464.3389770 |
| Temuan utama | Abstrak: sistem umumnya mempartisi data ke row group menurut waktu kedatangan; jumlah blok yang diakses berhubungan langsung dengan biaya I/O; qd-tree mencapai dalam 2× batas bawah data skipping berdasarkan selektivitas |
| Relevansi | Memberi dasar formal hubungan selektivitas–blok yang diakses, yang menjadi inti H1–H4 |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### F3 Extensible Data Skipping

| Field | Isi |
|---|---|
| Penulis | Paula Ta-Shma, Guy Khazma, Gal Lushi, Oshrit Feder |
| Tahun / Venue / Jenis | 2020 · IEEE BigData 2020 · conference |
| DOI | 10.1109/BigData50022.2020.9377740 |
| Temuan utama | Abstrak: data skipping tingkat objek/file berbasis metadata terpusat; 3,6× lebih cepat dibanding kueri yang ditulis ulang untuk memanfaatkan min/max Parquet |
| Relevansi | Menunjukkan bahwa skipping tingkat file dan skipping tingkat footer Parquet memiliki biaya berbeda; relevan untuk L-01 |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### F4 The Impact of Columnar File Formats on SQL-on-Hadoop Engine Performance: A Study on ORC and Parquet

| Field | Isi |
|---|---|
| Penulis | Todor Ivanov, Matteo Pergolesi |
| Tahun / Venue / Jenis | 2019 (online; Crossref) · Concurrency and Computation: Practice and Experience · journal |
| DOI | 10.1002/cpe.5523 |
| Masalah & metode | Membandingkan format dan pengaturan parameternya pada engine yang sama (Hive, SparkSQL) dengan BigBench (TPCx-BB) |
| Temuan utama | Abstrak: pemilihan format dan konfigurasinya berpengaruh signifikan; Snappy memberi perbaikan hingga 7 % untuk Parquet pada SparkSQL |
| Relevansi | Preseden metodologis terdekat pada rentang 6–10 tahun: satu engine, satu faktor fisik divariasikan. Parameter spesifik yang divariasikan selain kompresi **belum diverifikasi** dari full text |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### F5 Presto: SQL on Everything

| Field | Isi |
|---|---|
| Penulis | Raghav Sethi, Martin Traverso, Dain Sundstrom, David Phillips, Wenlei Xie, Yutian Sun, Nezih Yegitbasi, Haozhun Jin, dkk. |
| Tahun / Venue / Jenis | 2019 · ICDE 2019 · conference |
| DOI | 10.1109/ICDE.2019.00196 |
| Relevansi | Rujukan arsitektur engine (leluhur Trino) untuk menjelaskan split dan penjadwalan pada Background §2.2 |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### F6 Is Big Data Performance Reproducible in Modern Cloud Networks?

| Field | Isi |
|---|---|
| Penulis | Alexandru Uta, Alexandru Custura, Dmitry Duplyakin, Ivo Jimenez, Jan Rellermeyer, dkk. |
| Tahun / Venue / Jenis | 2020 · USENIX NSDI 2020 · conference |
| Identifier | <https://www.usenix.org/conference/nsdi20/presentation/uta> |
| Temuan utama | Abstrak: komunitas sistem sering mengabaikan variabilitas saat eksperimen di cloud; workload big data mengalami perlambatan dan kurang dapat direplikasi |
| Relevansi | Dasar untuk protokol noise floor dan repetisi (C-02) |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (halaman resmi USENIX) |

#### F7 Taming Performance Variability

| Field | Isi |
|---|---|
| Penulis | Aleksander Maricq, Dmitry Duplyakin, Ivo Jimenez, Carlos Maltzahn, Ryan Stutsman, dkk. |
| Tahun / Venue / Jenis | 2018 · USENIX OSDI 2018 · conference |
| Identifier | <https://www.usenix.org/conference/osdi18/presentation/maricq> |
| Temuan utama | Abstrak: studi 10 bulan, sekitar 900.000 titik data dari 835 server; pelajaran tentang besaran variabilitas dan dampaknya pada kepercayaan hasil eksperimen, serta rekomendasi parameter eksperimen |
| Relevansi | Dasar untuk menurunkan jumlah repetisi dari variabilitas, bukan dari angka tetap |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (halaman resmi USENIX) |

#### F8 Fair Benchmarking Considered Difficult: Common Pitfalls in Database Performance Testing

| Field | Isi |
|---|---|
| Penulis | Mark Raasveldt, Pedro Holanda, Tim Gubner, Hannes Mühleisen |
| Tahun / Venue / Jenis | 2018 · DBTest Workshop @ SIGMOD 2018 · workshop |
| DOI | 10.1145/3209950.3209955 |
| Relevansi | Daftar jebakan benchmarking DBMS; berguna untuk bagian Threats to Validity |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

#### F9 ★ Access Path Selection in Main-Memory Optimized Data Systems: Should I Scan or Should I Probe?

| Field | Isi |
|---|---|
| Penulis | Michael S. Kester, Manos Athanassoulis, Stratos Idreos |
| Tahun / Venue / Jenis | 2017 · SIGMOD 2017 · conference |
| DOI | 10.1145/3035918.3064049 |
| Temuan utama | Abstrak (terpotong di OpenAlex): optimasi scan modern mendorong peninjauan ulang pertanyaan access path selection |
| Relevansi | Preseden konseptual untuk "crossover menurut selektivitas": keputusan scan vs probe bergantung pada selektivitas. DSIC-2604 memindahkan logika serupa ke dimensi granularitas data-file |
| Keterbatasan bukti | Full text tidak dapat diakses; rincian model dan titik impas **tidak diverifikasi**. Pada manuskrip, karya ini hanya boleh dikutip sebagai preseden konsep, bukan untuk angka tertentu |
| Bukti diperiksa | Abstrak (sebagian) |
| Status | **VERIFIED** (Crossref) |

#### F10 Skipping-Oriented Partitioning for Columnar Layouts

| Field | Isi |
|---|---|
| Penulis | Liwen Sun, Michael J. Franklin, Jiannan Wang, Eugene Wu |
| Tahun / Venue / Jenis | 2016 · PVLDB 10(4) · journal |
| DOI | 10.14778/3025111.3025123 |
| Temuan utama | Abstrak: GSOP mempertimbangkan skipping horizontal dan partisi vertikal sekaligus; mengurangi data yang dipindai |
| Relevansi | Konteks skipping pada layout kolumnar |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

---

## 7. Karya Seminal (lebih dari 10 tahun)

#### G1 Fine-Grained Partitioning for Aggressive Data Skipping

| Field | Isi |
|---|---|
| Penulis | Liwen Sun, Michael J. Franklin, Sanjay Krishnan, Reynold S. Xin |
| Tahun / Venue / Jenis | 2014 · SIGMOD 2014 · conference |
| DOI | 10.1145/2588555.2610515 |
| Temuan utama | Abstrak: efektivitas data skipping bergantung pada kecocokan skema blok dengan filter kueri |
| Alasan dimasukkan | Dikutip oleh F10 dan menjadi dasar kluster data skipping; berada sedikit di luar batas 10 tahun |
| Bukti diperiksa | Abstrak |
| Status | **VERIFIED** (Crossref) |

**Rujukan dataset (bukan penelitian terdahulu).** Averty, T., Nasios, I., Ray, C., & Piliouras, N. (2026). MMDEC: Multimodal maritime dataset on the English channel. *Data in Brief*. DOI 10.1016/j.dib.2026.112629 (**VERIFIED**, Crossref). Dataset: DOI 10.5281/zenodo.17491518.

---

## 8. Perbandingan DSIC-2604 dengan Penelitian Terdahulu

Tabel berikut hanya mengisi sel yang dapat dipastikan dari bagian paper yang dibaca. Tanda "—" berarti aspek tersebut tidak tampak pada abstrak/full text yang diperiksa, bukan berarti pasti tidak ada.

| Dimensi | A1 Smart Compaction 2026 | A2 LST-Bench 2024 | A4 Javeri 2026 | B1 Zeng 2023 | D1 Nurdin 2026 | D3 Szoke 2026 | F2 Qd-tree 2020 | F4 Ivanov 2019 | **DSIC-2604 (rencana)** |
|---|---|---|---|---|---|---|---|---|---|
| Ukuran/jumlah data-file sebagai faktor | Ya (8 KB–128 MB, sintetis) | Tidak langsung (via evolusi tabel) | Diukur, bukan faktor | — | — | — | Ukuran blok bukan faktor | Konfigurasi format | **Ya, 4 level terkontrol** |
| Selektivitas sebagai faktor terkalibrasi | Tidak | — | — | Ya (konfigurasi workload) | — | — | Ya (untuk layout) | — | **Ya, 6 band, measured** |
| Row-group dipisahkan dari ukuran file | Tidak | — | — | Row-group dibahas; ukuran file tidak | — | — | — | — | **Ya (kontrol utama)** |
| Table format lakehouse (Iceberg dsb.) | Iceberg | Delta/Iceberg/Hudi | Iceberg/Hudi/Delta | Tidak | Iceberg | Beberapa | Tidak | Tidak | **Iceberg** |
| Engine | Spark-local | Spark, Trino | Spark | Beberapa | Trino | 11 engine | — | Hive, SparkSQL | **Trino** |
| Object store | — | Cloud | MinIO | — | Cloud | Lokal | — | HDFS | **MinIO lokal** |
| Sumber daya terbatas / satu node | Spark-local | Tidak | — | — | Tidak | Ya (4 core) | — | Tidak | **Ya (8 vCPU/16 GB)** |
| Repetisi terukur per kondisi | 3 | — | — | — | 5 | — | — | — | **20 (+2 warm-up)** |
| CI / uji statistik pada efek layout | Tidak pada benchmark kueri | — | — | — | CV | — | — | — | **Paired bootstrap 95 % CI, Holm** |
| Kriteria crossover dibekukan sebelum pengukuran | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | **Ya** |
| Telemetri mekanisme | Jumlah task (dijelaskan) | Metrik LST-Bench | Jumlah file | Mikro-benchmark format | Faktor variansi | — | Blok diakses | — | **Input bytes, split, CPU, memori** |
| Biaya write/maintenance | Ya (compaction) | Ya | Ya (write) | — | — | — | — | — | **Ya (RQ4)** |
| Data nyata non-TPC | Tidak (sintetis + TPC-H) | TPC-DS | — | Workload nyata + sintetis | Benchmark | TPC-H | Nyata + benchmark | TPCx-BB | **Ya (AIS MMDEC)** |
| Skala data | Kecil–menengah | Besar | — | Beragam | 1 GB–1 TB | SF 1, 10 | Besar | Besar | **~430 MiB (kecil)** |

**Pembacaan tabel.** Secara desain, DSIC-2604 berbeda paling jelas pada tiga hal: (1) selektivitas dan ukuran file disilangkan sebagai dua faktor terkontrol, (2) row-group dipisahkan dari ukuran file, dan (3) kriteria crossover serta protokol statistik dibekukan sebelum pengukuran. Sebaliknya, DSIC-2604 paling lemah pada **skala data** (~430 MiB, jauh di bawah karya lain) dan pada **realisme object store** (MinIO lokal). Kedua kelemahan ini perlu ditulis terbuka sebagai batas klaim, bukan ditutupi.

---

## 9. Analisis Gap: Apa yang Sudah Dijawab, Apa yang Masih Terbuka, dan Apakah DSIC-2604 Menutupnya

### 9.1 Hal yang sudah dijawab penelitian terdahulu (tidak boleh diklaim sebagai kontribusi DSIC-2604)

| Pengetahuan yang sudah mapan | Sumber |
|---|---|
| File kecil yang berlebihan menurunkan performa kueri dan menambah biaya metadata | A3 AutoComp; A1 Smart Compaction; F1 Delta Lake |
| Efek compaction/ukuran file bergantung pada workload | A1; A2 (via A1) |
| Pengurangan jumlah file dapat menurunkan paralelisme dan memperlambat full-scan | A1 (0,45–0,76×) |
| Data skipping berbasis zone map efektif hanya bila data terklaster selaras dengan predikat | B1 Zeng; C1 Ding; G1 Sun |
| Jumlah blok yang diakses berkaitan dengan selektivitas dan menentukan I/O | F2 Qd-tree; C2 Pando |
| Request kecil ke object store mahal karena latency round-trip | B3 Durner |
| Pilihan konfigurasi lakehouse saling berinteraksi; tidak ada konfigurasi terbaik universal | A6 LakeHelm; F4 Ivanov |
| Keputusan akses (scan vs probe) memiliki titik impas menurut selektivitas | F9 Kester (konsep) |
| Variansi runtime lakehouse Trino/Iceberg signifikan dan harus diukur | D1 Nurdin; F6 Uta; F7 Maricq |
| Lakehouse untuk data kapal/maritim | E3 Park |

Konsekuensinya, kalimat seperti "file kecil memperlambat kueri", "ukuran optimal bergantung pada workload", atau "crossover selektivitas" **bukan** kontribusi baru bila berdiri sendiri. Kontribusi DSIC-2604 hanya dapat berada pada **kuantifikasi terkontrol** dari interaksi tersebut.

### 9.2 Gap yang tampak nyata dan hubungannya dengan DSIC-2604

| Kode | Gap | Bukti adanya gap | Apakah desain DSIC-2604 menutupnya? | Status bukti saat ini | Pemblokir |
|---|---|---|---|---|---|
| **GAP-1** | Belum ditemukan studi yang menyilangkan ukuran data-file dan *measured selectivity* sebagai dua faktor terkontrol pada lakehouse | A1 tidak memiliki sumbu selektivitas; B1 dan F2 memiliki selektivitas tetapi tidak memvariasikan ukuran data-file; A2/A4 membandingkan format | **Ya, secara desain** | **Belum ditutup**, E3 belum dijalankan | C-01, C-03, G5 |
| **GAP-2** | Efek ukuran file belum dipisahkan dari ukuran row-group | A1 tidak mengendalikan row-group; B1 membahas row-group tanpa ukuran file | **Ya, secara desain**, dan ini pembeda terkuat | Belum ditutup; G4 belum diuji | L-01 (perumusan ulang H2/H4), N-04 |
| **GAP-3** | Studi ukuran file/compaction memakai repetisi sedikit tanpa CI dan tanpa kriteria yang dibekukan | A1: 3 run, median; D2 menunjukkan praktik pelaporan yang lemah di bidang ini | **Ya**: 20 repetisi berpasangan, bootstrap CI, crossover dibekukan | Belum ditutup; protokol ada, data belum ada | **C-02** (noise floor tidak sahih) |
| **GAP-4** | Perilaku layout lakehouse pada host tunggal bersumber daya terbatas | D3 mengevaluasi engine pada satu node, bukan layout; A1 Spark-local tanpa definisi sumber daya | **Sebagian**: definisi resource-constrained ada di README | Belum ditutup; spesifikasi host belum dibekukan | M-01, M-02 |
| **GAP-5** | Keputusan layout yang memperhitungkan biaya write bersyarat pada selektivitas | C3 OReO dan A3 AutoComp menyeimbangkan manfaat dan biaya, tetapi tidak per band selektivitas | **Sebagian** (RQ4 + E6 decision map) | Belum ditutup | E1/H6 belum berjalan |
| **GAP-6** | Mayoritas studi memakai TPC-H/TPC-DS atau data sintetis | A1 (sintetis + TPC-H), D3 (TPC-H), A2 (TPC-DS) | **Ya**: AIS nyata dengan distribusi temporal tidak seragam | Data tervalidasi (G1 lulus dengan catatan) | M-05, M-06 |

**Catatan kejujuran.** GAP-1 dan GAP-2 adalah gap yang *didukung pencarian*, bukan gap yang *terverifikasi eksternal secara sistematis*. Pencarian 2026-09-27 mencakup 11 kueri Google Scholar dan verifikasi Crossref/arXiv, tetapi tidak mencakup telusur sitasi penuh, database IEEE/ACM langsung, atau literatur industri (blog teknis vendor). Studi identik dapat saja ada di luar cakupan ini.

### 9.3 Apakah DSIC-2604 saat ini benar-benar menutup gap tersebut?

**Belum.** Ketiga faktor berikut harus terpenuhi agar GAP-1 sampai GAP-3 dapat diklaim tertutup:

1. **Desain harus dapat memisahkan ukuran file dari paralelisme.** Smart Compaction (A1) menunjukkan bahwa perubahan jumlah file dapat mengubah latency 0,45–0,76× hanya karena paralelisme. Bila kondisi 64 MiB hanya berisi 6–7 file (C-01), efek yang terukur pada ujung grid tidak dapat diatribusikan pada ukuran file. Tanpa penyelesaian D-01, GAP-1 tidak dapat ditutup secara bersih.
2. **Noise floor harus sahih.** Kontribusi metodologis GAP-3 hilang bila ambang penafsiran berasal dari artefak alat ukur (C-02).
3. **Hipotesis mekanisme harus sesuai dengan kontrol yang dipakai.** Bila H2 tidak dirumuskan ulang (L-01), GAP-2 berisiko dilaporkan sebagai "hipotesis ditolak" alih-alih sebagai temuan tentang granularitas pruning.

---

## 10. Risiko Klaim Novelty dan Rumusan Posisi yang Aman

### 10.1 Klaim yang harus dihindari

| Klaim berisiko | Alasan |
|---|---|
| "Penelitian pertama tentang ukuran file Parquet" | A1, A3, F4 sudah meneliti ukuran file/konfigurasi format |
| "Menemukan ukuran file optimal" | Bertentangan dengan klaim negatif mahasiswa sendiri dan dengan A6/F4 |
| "Crossover selektivitas adalah konsep baru" | Konsep sudah ada pada access path selection (F9) |
| "Hasil berlaku untuk lakehouse cloud" | MinIO lokal dan tabel ~430 MiB; B3 menunjukkan perilaku object store cloud berbeda |
| "Noise floor lakehouse sekitar 8 %, sejalan dengan literatur" | Tidak sebanding dengan D1 (L-03) |

### 10.2 Rumusan posisi yang disarankan (untuk pertimbangan Supervisor 1)

Bahasa Indonesia (skripsi):

> Penelitian terdahulu telah menunjukkan bahwa file kecil yang berlebihan menambah overhead metadata dan bahwa manfaat compaction bergantung pada workload. Namun, pada studi yang ditelusuri, ukuran data-file belum diuji secara terkontrol bersama *measured selectivity* sambil menahan ukuran row-group tetap. Penelitian ini mengisi celah tersebut pada skala tabel ratusan MiB dan lakehouse satu host, dengan kriteria crossover yang dibekukan sebelum pengukuran.

English (article):

> Prior work shows that small-file proliferation increases metadata overhead and that the benefit of compaction is workload-dependent. However, among the studies we reviewed, data-file size has not been varied jointly with measured query selectivity while holding row-group size fixed. We quantify this interaction on a single-host, resource-constrained Iceberg/Trino lakehouse at the scale of hundreds of MiB, using a crossover criterion frozen before measurement.

Kedua rumusan sengaja memakai "pada studi yang ditelusuri" / "among the studies we reviewed" sampai verifikasi literatur final selesai.

---

## 11. Rekomendasi

### R-1 — Rumuskan ulang H2 dan H4 sesuai kontrol row-group (menanggapi L-01)

**Masalah.** H2 mengandalkan pengurangan physical input oleh file kecil, padahal pruning row-group yang identik pada semua varian diduga menghilangkan sebagian besar keuntungan tersebut.
**Mengapa penting.** Tanpa perumusan ulang, hasil yang paling mungkin akan dilaporkan sebagai kegagalan hipotesis, padahal sebenarnya merupakan jawaban atas pertanyaan yang lebih tajam.

| Opsi | Isi | Keuntungan | Biaya / risiko |
|---|---|---|---|
| **A** | Pertahankan desain; rumuskan H2 sebagai *"pada row-group tetap, file kecil tidak mengurangi physical input secara bermakna; perbedaan latency berasal dari overhead per file"* dan H4 sebagai perbandingan pruning tingkat file vs tingkat row-group. Tambah metrik jumlah file yang dipangkas dan dibaca bila telemetri Trino/Iceberg menyediakannya | Tidak menambah eksperimen; kontribusi GAP-2 menjadi eksplisit | Harus dilakukan **sebelum** E3 dan dicatat bertanggal agar tidak menjadi perubahan post-hoc |
| B | Tambah ukuran row-group sebagai faktor kedua | Menguji interaksi tiga arah | Eksperimen meledak (×2–×4 kondisi); tidak realistis dalam jadwal 4 minggu |
| C | Biarkan H2 apa adanya | Tidak ada pekerjaan | H2 kemungkinan ditolak tanpa narasi yang jelas; posisi publikasi melemah |

**Rekomendasi: Opsi A.** *SUPERVISOR-1 DECISION REQUIRED (D-04).*
**Bukti penutupan:** H2/H4 baru tercatat di `protocol_freeze.yaml` dengan tanggal sebelum run E3 pertama; ada satu `EXPLAIN ANALYZE` per varian pada satu band yang menunjukkan jumlah file/row-group yang dibaca.

### R-2 — Periksa dan beri label mekanisme Q1 (menanggapi L-02)

| Opsi | Isi | Biaya |
|---|---|---|
| **A** | Pertahankan Q1; verifikasi dengan `EXPLAIN ANALYZE` apakah Trino membaca data atau hanya metadata; laporkan Q1 sebagai kueri dominan-metadata dan pisahkan interpretasinya dari Q2/Q3 | Sekitar 1 jam |
| B | Ganti Q1 dengan scan proyeksi satu kolom (mis. `SUM` kolom numerik) | Mengubah template beku sebelum E3; perlu persetujuan |
| C | Hapus Q1 | Mengurangi kekuatan syarat replikasi lintas query family |

**Rekomendasi: Opsi A.** Keputusan B/C hanya diambil bila `EXPLAIN ANALYZE` menunjukkan Q1 tidak membaca data sama sekali.

### R-3 — Tutup C-01 dengan mempertimbangkan bukti A1

Keputusan D-01 tidak dibuka ulang di sini karena opsinya sudah tersedia di `supervision/03-dsic-2604/arahan-teknis-minggu-1.md` §2. Tambahan dari literatur: temuan paralelisme pada Smart Compaction (A1) menaikkan risiko publikasi C-01. Reviewer yang mengenal karya ini akan menanyakan jumlah file per kondisi. Opsi yang menjaga ≥ 8 file pada kondisi terbesar (atau mencatat split per kondisi sebagai kovariat) menjadi lebih penting daripada sebelumnya.

### R-4 — Tulis Related Work dari peta ini

Mahasiswa menulis `paper/manuscript.md` §3 dengan struktur minimal:

1. Lakehouse dan table format: E1, F1, A5, E2.
2. Ukuran file, compaction, dan maintenance: A1, A2, A3, C3.
3. Data skipping dan layout: G1, F2, C1, C2, B1.
4. Object store dan engine: B3, F5, D3.
5. Metodologi pengukuran: D2, F6, F7, F8, D1.
6. Posisi DSIC-2604: paragraf yang diturunkan dari §9.2, memakai rumusan §10.2.

Setiap karya harus dibaca sendiri oleh mahasiswa. Kartu pada §5–§7 adalah alat bantu supervisi, bukan pengganti membaca paper.

### R-5 — Jangan pakai literatur variansi untuk membenarkan 7,83 % (menanggapi L-03)

Setelah C-02 diperbaiki, D1 dan F7 dapat dikutip untuk menjelaskan **mengapa** noise floor diukur ulang dengan workload nyata dan telemetri Trino, bukan untuk membenarkan angka lama.

---

## 12. Keputusan yang Memerlukan Supervisor 1

| Kode | Perkara | Status | Memblokir |
|---|---|---|---|
| D-01 | Penetapan grid ukuran file | Menunggu (sejak 2026-09-12) | H6, H7, Minggu 2, GAP-1 |
| D-02 | Pencabutan aturan noise floor 7,83 % | Menunggu | Penafsiran Minggu 3, GAP-3 |
| D-03 | Rekonsiliasi periode 92/93 hari | Menunggu | H7 |
| **D-04** | **Perumusan ulang H2/H4 sesuai kontrol row-group (R-1 Opsi A)** | **Baru** | Validitas GAP-2; harus sebelum E3 |
| **D-05** | **Persetujuan rumusan posisi §10.2 sebagai kalimat jangkar sementara** | **Baru** | Penulisan Related Work dan abstrak |

**SUPERVISOR-1 DECISION REQUIRED** untuk D-04 dan D-05. Keduanya menyangkut hipotesis dan klaim kontribusi utama.

---

## 13. Definition of Done untuk Posisi Literatur

Posisi literatur DSIC-2604 dapat dinyatakan siap bila:

- [ ] `paper/manuscript.md` §3 memuat minimal kelima kluster pada R-4, dengan setiap rujukan memiliki DOI/identifier yang dapat dibuka;
- [ ] minimal A1, A2, B1, F2, dan F9 dikutip dan perbedaannya terhadap DSIC-2604 dijelaskan secara spesifik (faktor, kontrol, engine, repetisi);
- [ ] tidak ada klaim "pertama", "optimal universal", atau "novel" tanpa kualifikasi "pada studi yang ditelusuri";
- [ ] batas skala (~430 MiB) dan batas object store (MinIO lokal) tertulis di Threats to Validity dengan rujukan B3;
- [ ] H2/H4 telah dirumuskan ulang dan dibekukan sebelum E3 (D-04), atau keputusan untuk mempertahankannya tercatat;
- [ ] status preprint A1 dan D1 diperiksa ulang sebelum submit artikel; bila sudah terbit, rujukan diganti ke versi resmi;
- [ ] pencarian diperluas minimal ke ACM DL dan IEEE Xplore dengan kueri pada §15, dan hasilnya dicatat, sebelum klaim gap dinaikkan dari "didukung pencarian" menjadi "terverifikasi".

---

## 14. Daftar Pustaka Terverifikasi

Format ringkas APA. Status verifikasi pada kurung siku.

1. Armbrust, M., Das, T., Sun, L., Yavuz, B., Zhu, S., Murthy, M., Torres, J., van Hovell, H., et al. (2020). Delta Lake: High-performance ACID table storage over cloud object stores. *PVLDB, 13*(12). https://doi.org/10.14778/3415478.3415560 [VERIFIED]
2. Armbrust, M., Ghodsi, A., Xin, R., & Zaharia, M. (2021). Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics. *CIDR 2021*. https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf [VERIFIED]
3. Averty, T., Nasios, I., Ray, C., & Piliouras, N. (2026). MMDEC: Multimodal maritime dataset on the English channel. *Data in Brief*. https://doi.org/10.1016/j.dib.2026.112629 [VERIFIED]
4. Camacho-Rodríguez, J., Agrawal, A., Gruenheid, A., Gosalia, A., Petculescu, C., Aguilar-Saborit, J., Floratou, A., & Curino, C. (2024). LST-Bench: Benchmarking log-structured tables in the cloud. *Proc. ACM Manag. Data, 2*(1). https://doi.org/10.1145/3639314 [VERIFIED]
5. Cutura, J., & Prakash, S. (2026). Smart compaction: Predicting compaction utility from lakehouse table metadata. *arXiv:2608.08639*. [PARTIALLY VERIFIED — preprint]
6. Ding, J., Minhas, U. F., Chandramouli, B., Wang, C., Li, Y., Li, Y., Kossmann, D., & Gehrke, J. (2021). Instance-optimized data layouts for cloud analytics workloads. *SIGMOD 2021*. https://doi.org/10.1145/3448016.3457270 [VERIFIED]
7. Durner, D., Leis, V., & Neumann, T. (2023). Exploiting cloud object storage for high-performance analytics. *PVLDB, 16*(11). https://doi.org/10.14778/3611479.3611486 [VERIFIED]
8. Ginter, P., & Leis, V. (2026). Active data lakes: Regaining physical data independence without losing interoperability. *PVLDB*. https://doi.org/10.14778/3797919.3797941 [VERIFIED]
9. Gruenheid, A., Camacho-Rodríguez, J., Curino, C., Ramakrishnan, R., Pak, S., Sakdeo, S., Gandhi, L., & Singhal, S. K. (2025). AutoComp: Automated data compaction for log-structured tables in data lakes. *Companion of SIGMOD 2025*. https://doi.org/10.1145/3722212.3724430 [VERIFIED]
10. Hansert, P., & Michel, S. (2022). Ameliorating data compression and query performance through cracked Parquet. *BiDEDE Workshop @ SIGMOD 2022*. https://doi.org/10.1145/3530050.3532923 [VERIFIED]
11. Ivanov, T., & Pergolesi, M. (2019). The impact of columnar file formats on SQL-on-Hadoop engine performance: A study on ORC and Parquet. *Concurrency and Computation: Practice and Experience*. https://doi.org/10.1002/cpe.5523 [VERIFIED]
12. Jain, P., Kraft, P., Power, C., Das, T., Stoica, I., & Zaharia, M. (2023). Analyzing and comparing lakehouse storage systems. *CIDR 2023*. https://www.cidrdb.org/cidr2023/papers/p92-jain.pdf [VERIFIED]
13. Javeri, V. S. (2026). An empirical study of open lakehouse table formats on object storage. *IEEE SoutheastCon 2026*. https://doi.org/10.1109/southeastcon63549.2026.11475985 [VERIFIED]
14. Kester, M. S., Athanassoulis, M., & Idreos, S. (2017). Access path selection in main-memory optimized data systems: Should I scan or should I probe? *SIGMOD 2017*. https://doi.org/10.1145/3035918.3064049 [VERIFIED]
15. Leis, V., & Kuschewski, M. (2021). Towards cost-optimal query processing in the cloud. *PVLDB*. https://doi.org/10.14778/3461535.3461549 [VERIFIED]
16. Li, Y., Lu, J., & Chandramouli, B. (2023). Selection pushdown in column stores using bit manipulation instructions. *Proc. ACM Manag. Data*. https://doi.org/10.1145/3589323 [VERIFIED]
17. Liu, C., Pavlenko, A., Interlandi, M., & Haynes, B. (2023). A deep dive into common open formats for analytical DBMSs. *PVLDB, 16*(11). https://doi.org/10.14778/3611479.3611507 [VERIFIED]
18. Maricq, A., Duplyakin, D., Jimenez, I., Maltzahn, C., Stutsman, R., et al. (2018). Taming performance variability. *USENIX OSDI 2018*. https://www.usenix.org/conference/osdi18/presentation/maricq [VERIFIED]
19. Mark-Andor, S. (2026). Modern alternatives to Hive: A systematic review and single-node benchmark of SQL-on-Hadoop and lakehouse engines. *Information Systems*. https://doi.org/10.1016/j.is.2025.102635 [VERIFIED]
20. Nurdin, J., Liu, W., Mccreadie, R., & Thamsen, L. (2026). Predicting lakehouse performance in clouds: An empirical exploration of query runtime variance. *arXiv:2606.03464* (dinyatakan akan terbit di IEEE CLOUD 2026). [PARTIALLY VERIFIED — preprint]
21. Papadopoulos, A. V., Versluis, L., Bauer, A., Herbst, N., von Kistowski, J., Ali-Eldin, A., Abad, C. L., & Amaral, J. N. (2021). Methodological principles for reproducible performance evaluation in cloud computing. *IEEE TSE*. https://doi.org/10.1109/TSE.2019.2927908 [VERIFIED]
22. Park, S., Yang, C.-S., & Kim, J. (2023). Design of vessel data lakehouse with big data and AI analysis technology for vessel monitoring system. *Electronics, 12*(8), 1943. https://doi.org/10.3390/electronics12081943 [VERIFIED]
23. Raasveldt, M., Holanda, P., Gubner, T., & Mühleisen, H. (2018). Fair benchmarking considered difficult: Common pitfalls in database performance testing. *DBTest @ SIGMOD 2018*. https://doi.org/10.1145/3209950.3209955 [VERIFIED]
24. Rong, K., Liu, P., Sonje, S. A., & Charikar, M. (2024). Dynamic data layout optimization with worst-case guarantees. *ICDE 2024*. https://doi.org/10.1109/icde60146.2024.00327 [VERIFIED]
25. Schneider, J., Gröger, C., Lutsch, A., Schwarz, H., & Mitschang, B. (2024). The lakehouse: State of the art on concepts and technologies. *SN Computer Science*. https://doi.org/10.1007/s42979-024-02737-0 [VERIFIED]
26. Sethi, R., Traverso, M., Sundstrom, D., Phillips, D., Xie, W., Sun, Y., Yegitbasi, N., Jin, H., et al. (2019). Presto: SQL on everything. *ICDE 2019*. https://doi.org/10.1109/ICDE.2019.00196 [VERIFIED]
27. Sudhir, S., Tao, W., Laptev, N., Habis, C., Cafarella, M., & Madden, S. (2023). Pando: Enhanced data skipping with logical data partitioning. *PVLDB, 16*(9). https://doi.org/10.14778/3598581.3598601 [VERIFIED]
28. Sun, L., Franklin, M. J., Krishnan, S., & Xin, R. S. (2014). Fine-grained partitioning for aggressive data skipping. *SIGMOD 2014*. https://doi.org/10.1145/2588555.2610515 [VERIFIED]
29. Sun, L., Franklin, M. J., Wang, J., & Wu, E. (2016). Skipping-oriented partitioning for columnar layouts. *PVLDB, 10*(4). https://doi.org/10.14778/3025111.3025123 [VERIFIED]
30. Ta-Shma, P., Khazma, G., Lushi, G., & Feder, O. (2020). Extensible data skipping. *IEEE BigData 2020*. https://doi.org/10.1109/BigData50022.2020.9377740 [VERIFIED]
31. Uta, A., Custura, A., Duplyakin, D., Jimenez, I., Rellermeyer, J., et al. (2020). Is big data performance reproducible in modern cloud networks? *USENIX NSDI 2020*. https://www.usenix.org/conference/nsdi20/presentation/uta [VERIFIED]
32. Xu, Z., Dong, S., Gong, H., Pham, D., & Ma, L. (2026). LakeHelm: Zero-shot lakehouse advisor for joint engine-format selection and configuration. *PVLDB*. https://doi.org/10.14778/3811243.3811250 [VERIFIED]
33. Yang, Z., Chandramouli, B., Wang, C., Gehrke, J., Li, Y., Minhas, U. F., Larson, P.-Å., & Kossmann, D. (2020). Qd-tree: Learning data layouts for big data analytics. *SIGMOD 2020*. https://doi.org/10.1145/3318464.3389770 [VERIFIED]
34. Zeng, X., Hui, Y., Shen, J., Pavlo, A., McKinney, W., & Zhang, H. (2023). An empirical evaluation of columnar storage formats. *PVLDB, 17*(2). https://doi.org/10.14778/3626292.3626298 [VERIFIED]

*Catatan:* Rujukan no. 3 adalah artikel dataset, bukan penelitian terdahulu, sehingga jumlah penelitian terdahulu yang diulas adalah 33. Venue ICDE untuk no. 24 terkonfirmasi melalui Crossref; status terbit no. 5 dan no. 20 belum terkonfirmasi.

---

## 15. Lampiran: Log Pencarian

**Tanggal:** 2026-09-27 · **Pelaksana:** Supervisor 1

### 15.1 Google Scholar

| # | Kueri | Filter tahun | Karya terpilih |
|---|---|---|---|
| 1 | `parquet "file size" "selectivity" query latency` | ≥ 2016 | B1, B2 |
| 2 | `"small files" lakehouse Iceberg query performance compaction` | ≥ 2016 | A1 |
| 3 | `data skipping "zone maps" block size trade-off columnar` | ≥ 2016 | C1, C2, F2 |
| 4 | `Trino Iceberg benchmark "file size"` | ≥ 2016 | A2, A3, B5 |
| 5 | `"row group size" Parquet performance evaluation` | ≥ 2016 | B1, F4 |
| 6 | `"access path selection" "scan or should I probe"` | — | F9 |
| 7 | `smooth scan robust access path selectivity` | — | (tidak dipilih; abstrak tidak tersedia) |
| 8 | `taming performance variability experiments repetitions` | — | F6, F7 |
| 9 | `lakehouse query runtime variance empirical` | — | D1, D3, A6 |
| 10 | `AIS vessel data Parquet big data query storage evaluation` | ≥ 2021 | E3 |
| 11 | `Iceberg Trino MinIO lakehouse performance evaluation` | ≥ 2021 | E2 |

### 15.2 Crossref (`query.bibliographic`)

`Pando enhanced data skipping` · `Extensible data skipping Ta-Shma` · `Selection pushdown in column stores` · `AutoComp automated data compaction` · `Towards cost-optimal query processing in the cloud` · `F3 open-source data file format` · `Analyzing and comparing lakehouse storage systems` · `data file size query selectivity lakehouse Parquet` · `single-node lakehouse benchmark MinIO Trino Iceberg` · `Iceberg file size compaction query performance Trino` · `Dynamic Data Layout Optimization with Worst-case Guarantees`

### 15.3 Web search (pelengkap)

`LST-Bench benchmarking log-structured tables` · `OREO data layout reorganization data skipping` · `arXiv 2510.15445 Optimizing Data Lakes' Queries` · `Jain Analyzing and Comparing Lakehouse Storage Systems CIDR 2023`

### 15.4 Kandidat yang ditemukan tetapi tidak dimasukkan

| Karya | Alasan |
|---|---|
| Weintraub (2025), *Optimizing Data Lakes' Queries*, arXiv:2510.15445 | Tesis tentang strategi transfer storage–compute; relevansi terhadap ukuran file belum diperiksa dari full text |
| Borovica-Gajic et al. (2018), Smooth Scan, *VLDB Journal* | Abstrak tidak tersedia; F9 sudah mewakili konsep crossover selektivitas |
| Lakkireddy (2026), *JAIT* | Benchmark fungsional format; tidak menyentuh ukuran file × selektivitas |
| Beberapa artikel jurnal non-indeks (IJRPETM, IJAM, sarcouncil) | Kualitas venue dan metodologi tidak dapat dinilai; tidak dipakai sebagai pembanding |
| Blog/Medium tentang tuning Parquet | Bukan publikasi ilmiah |
