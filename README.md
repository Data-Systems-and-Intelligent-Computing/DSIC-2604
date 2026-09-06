# DSIC-2604 — Parquet Data-File Size × Query Selectivity

Repository penelitian **DSIC-2604** untuk eksperimen data systems mengenai interaksi ukuran data-file Parquet dan measured query selectivity pada lakehouse bersumber daya terbatas.

Dataset benchmark: **MMDEC** — [10.5281/zenodo.17491518](https://doi.org/10.5281/zenodo.17491518),
artikel data [10.1016/j.dib.2026.112629](https://doi.org/10.1016/j.dib.2026.112629)
(salinan di `refs/`).

Judul skripsi yang direkomendasikan:

> **Interaksi Ukuran Data-File Parquet dan Selektivitas Query pada Lakehouse Bersumber Daya Terbatas: Evaluasi Terkontrol Menggunakan MMDEC**

Judul artikel yang direkomendasikan:

> **Parquet Data-File Size–Query Selectivity Interactions in a Resource-Constrained Lakehouse: A Controlled Study on MMDEC**

---

## Keputusan Pembimbing

Penelitian ini **tidak** diarahkan untuk mencari satu ukuran file Parquet yang “optimal” secara universal.

Ukuran data-file yang menguntungkan bergantung pada:
- query selectivity;
- row order;
- row-group granularity;
- compression;
- partitioning;
- query engine;
- object-store behavior;
- jumlah file;
- split scheduling;
- CPU/RAM/storage/network budget.

Karena itu, kontribusi yang diterima adalah **controlled interaction study**.

Pertanyaan yang diuji:

> **Bagaimana ukuran data-file Parquet berinteraksi dengan measured query selectivity dalam memengaruhi analytical query latency ketika row-group size, row order, partitioning, compression, query engine, dan hardware dibuat tetap?**

Output akhir sebaiknya berupa:

```text
conditional crossover / decision map
```

bukan:

```text
one universal best Parquet file size
```

Tidak ditemukan crossover juga merupakan hasil yang sah.

---

## Kalimat Jangkar Penelitian

> Penelitian ini menguji secara terkontrol bagaimana ukuran data-file Parquet berinteraksi dengan measured query selectivity pada lakehouse bersumber daya terbatas, sambil mengendalikan row-group granularity dan faktor physical-layout lain, kemudian menjelaskan perubahan relative performance menggunakan telemetry I/O, split, CPU, memory, serta write/maintenance cost.

---

## Posisi Penelitian

Penelitian ini berada pada **Data Systems**.

MMDEC hanya berfungsi sebagai **real Parquet benchmark dataset**.

Novelty bukan:
- data maritim;
- MinIO;
- Iceberg;
- Trino;
- Parquet;
- mencoba beberapa ukuran file.

Novelty yang aman adalah:

> **controlled file-size × measured-selectivity interaction study dengan fixed row-group granularity, predefined crossover criterion, resource constraints, dan mechanism attribution.**

---

## Research Question

### RQ Utama

**RQ1. Bagaimana ukuran data-file Parquet berinteraksi dengan query selectivity dalam memengaruhi analytical query latency pada lakehouse bersumber daya terbatas ketika row-group size, row order, partitioning, compression, query engine, dan hardware dibuat tetap?**

### Sub-RQ

**RQ2.** Apakah relative ranking antarukuran data-file berubah pada selectivity tertentu sehingga membentuk crossover region yang stabil antar-pengulangan dan query family?

**RQ3.** Mekanisme sistem apa yang menjelaskan perubahan tersebut, dilihat dari physical input bytes, processed rows/bytes, split activity, CPU utilization, dan peak memory?

**RQ4.** Berapa biaya layout generation/write dan compaction/rewrite yang ditimbulkan tiap file-size regime, dan apakah rekomendasi read-side berubah ketika write/maintenance cost ikut dipertimbangkan?

**RQ5 — Article robustness.** Apakah pola file-size–selectivity tetap terlihat pada row-order control atau tabel MMDEC kedua?

RQ5 bukan syarat minimum kelulusan.

---

## Hipotesis

### H1 — Interaction

Efek file size terhadap latency bergantung pada measured query selectivity.

Bukti yang mendukung:
- paired difference berubah sistematis sepanjang selectivity axis;
- interaction term/contrast jelas;
- arah cukup stabil antar-query-family utama.

Hasil yang membatalkan:
- perbedaan relatif konstan;
- confidence interval terlalu lebar;
- tidak ada pola interaction yang dapat dibedakan dari noise.

### H2 — Low-Selectivity Benefit

Pada selectivity rendah, satu atau lebih file-size lebih kecil dapat mengurangi latency atau physical input dibanding 128/256 MiB.

Ini hipotesis, bukan asumsi.

### H3 — Crossover

Relative winner berubah dari ukuran lebih kecil ke lebih besar ketika selectivity meningkat.

Crossover hanya boleh diklaim setelah criterion yang sudah dibekukan terpenuhi.

### H4 — Mechanism

Perubahan latency dapat dijelaskan oleh trade-off:

```text
data skipping / physical-input reduction
vs
file-open / split / scheduling overhead
```

### H5 — Write Trade-off

File yang lebih kecil diperkirakan meningkatkan:
- generated file count;
- layout-build time;
- compaction/rewrite cost.

Semua hipotesis boleh ditolak.

---

## Dataset

### Sumber dan Sitasi

Dataset: **MMDEC — Multimodal Maritime Dataset on the English Channel**

```text
DOI dataset  : 10.5281/zenodo.17491518
DOI artikel  : 10.1016/j.dib.2026.112629
Lisensi      : CC BY-NC 4.0 (artikel); periksa lisensi record Zenodo untuk data
```

> Averty, T., Nasios, I., Ray, C., Piliouras, N. (2026). MMDEC: Multimodal
> maritime dataset on the English channel. *Data in Brief*, 65, 112629.

PDF artikel tersimpan di `refs/`. Repository ini **tidak** meredistribusi data
MMDEC — hanya manifest, checksum, metadata layout, dan hasil pengukuran.

### Primary

```text
Dataset_AIS_POS.parquet
```

Target yang harus diverifikasi terhadap artikel (gate G1):

```text
19,014,229 AIS position messages
25,130 MMSI unik
periode 1 Juli - 30 September 2023 (92 hari)
message types 1, 2, 3, 18, 19, 27
```

Kolom menurut **Tabel 2 artikel** (14 kolom, nama persis):

| Kolom | Peran dalam eksperimen |
|---|---|
| `Date` | sumbu predikat untuk kalibrasi selectivity (Q1-Q3) |
| `Mmsi` | entity robustness (Q4) |
| `MessageType` | kunci GROUP BY pada Q3 (maksimal 6 grup) |
| `SpeedOverGround` | kolom teragregasi pada Q2 dan Q3 |
| `Latitude`, `Longitude` | payload; tidak dipakai sebagai predikat |
| `Source`, `NavigationStatus`, `PositionAccuracy` | payload |
| `CourseOverGroundDegrees`, `RateOfTurn`, `TrueHeadingDegrees` | payload |
| `chunk_folder`, `id_chunk` | kolom kurasi; `id_chunk` bertipe **daftar**, keduanya dapat NaN |

Tiga konsekuensi yang mengikat desain:

1. **`Date` harus bertipe temporal.** Jika snapshot menyimpannya sebagai
   string, predikat `BETWEEN TIMESTAMP` dan min/max statistics berperilaku
   berbeda. Selesaikan di E0 dengan memperbaiki canonical snapshot, **bukan**
   dengan `CAST` di dalam query — cast menghalangi pruning dan mengubah
   konstruk yang sedang diukur. Diperiksa oleh `src/validate_source.py`.
2. **`id_chunk` bertipe `list`.** Rewrite layout harus mempertahankan tipe
   nested-nya; mengubahnya menjadi string akan mengubah ukuran file dan
   melanggar semantic equivalence.
3. **Q3 hanya menghasilkan <= 6 grup.** Ini konsisten dengan tujuan Q3
   (agregasi ringan), tetapi harus dinyatakan eksplisit di manuskrip agar
   pembaca tidak mengira Q3 menguji tekanan hash aggregation.

Sentinel "tidak tersedia" pada Tabel 2: `CourseOverGroundDegrees` = 511,
`TrueHeadingDegrees` = 511, `RateOfTurn` = +/-128. Artikel tidak menyebut
sentinel untuk `SpeedOverGround`; periksa distribusinya saat EDA dan catat
keputusannya. Perlakuannya harus identik di keempat layout variant.

### Secondary

Setelah main study selesai:

```text
Dataset_AIS_SPEC.parquet   13,558,007 status messages | 23,958 MMSI unik
Dataset_BATHYMETRY.parquet 12,386,244 data points
```

Secondary table adalah external robustness, bukan bagian wajib main factorial grid.

Catatan: 1.172 vessel di AIS_POS tidak memiliki status message padanan
(artikel MMDEC). Relevan bila robustness melibatkan join; tidak relevan untuk
main grid.

---

## Mengapa AIS_POS?

AIS_POS cocok karena:
1. jumlah baris cukup besar;
2. native Parquet;
3. memiliki temporal axis;
4. `Date` memungkinkan calibrated range predicates;
5. `Mmsi` memungkinkan entity robustness;
6. physical layout dapat direwrite tanpa mengubah semantics;
7. tidak perlu data sintetis sebagai benchmark utama.

---

## Arsitektur Eksperimen

```text
MMDEC source snapshot
        ↓
canonical AIS_POS
        ↓
fixed:
- row order
- row-group target
- compression
- partitioning
- schema
- writer
        ↓
keputusan grid berdasarkan ukuran tabel kanonik
        ↓
controlled data-file variants
        ├── 32 MiB          (fallback:   8 MiB)
        ├── 64 MiB          (fallback:  16 MiB)
        ├── 128 MiB ← baseline (fallback: 32 MiB ← baseline)
        └── 256 MiB         (fallback:  64 MiB)
        ↓
MinIO
        ↓
Iceberg (REST catalog)
        ↓
Trino
        ↓
query harness
        ↓
Trino telemetry + host telemetry
        ↓
raw run logs
        ↓
paired analysis
        ↓
crossover / no-crossover map
        ↓
mechanism attribution
```

Spark/PySpark dipakai untuk controlled layout generation, bukan sebagai query-engine pembanding.

---

## Faktor Eksperimen

### Faktor A — Data-File Size

Primary grid:

```text
32 MiB
64 MiB
128 MiB
256 MiB
```

Baseline:

```text
128 MiB
```

Opsional:

```text
512 MiB
```

Aturan jumlah file minimum berlaku untuk **seluruh grid**, bukan hanya 512 MiB:

```text
kondisi file-size terbesar harus menghasilkan >= 8 file
lebih baik >= 16 file
```

Di bawah ambang itu, jumlah split terlalu sedikit untuk membedakan efek
file-size dari efek paralelisme.

#### Kelayakan grid bergantung pada ukuran tabel kanonik

`Dataset_AIS_POS.parquet` berisi 19.014.229 baris dengan 14 kolom. Setelah
Snappy, ukuran tabel yang realistis berada di kisaran ratusan MiB sampai
sekitar 1 GiB. Proyeksinya:

| Ukuran tabel kanonik | file @32 MiB | @64 MiB | @128 MiB | @256 MiB | Grid utama layak? |
|---:|---:|---:|---:|---:|---|
| ~500 MiB | 15 | 7 | 3 | 1 | tidak |
| ~900 MiB | 28 | 14 | 7 | 3 | tidak |
| ~1,5 GiB | 48 | 24 | 12 | 6 | tidak |
| ~2 GiB | 64 | 32 | 16 | 8 | ya (batas) |
| >= 4 GiB | 128 | 64 | 32 | 16 | ya |

Artinya grid 32/64/128/256 MiB **tidak dapat diasumsikan layak**. Ukuran tabel
kanonik wajib diukur lebih dulu (E0/E1), lalu grid dipilih dengan aturan beku:

```text
ukur ukuran tabel kanonik
        |
        v
proyeksikan jumlah file pada kondisi terbesar
        |
        +-- >= 8 file  --> pakai grid utama 32/64/128/256 MiB
        |                  (row-group target 32 MiB)
        |
        +-- <  8 file  --> pakai fallback grid 8/16/32/64 MiB
                           (row-group target 8 MiB, baseline 32 MiB)
```

Fallback grid mempertahankan rasio yang sama (4x antar-kondisi ujung, 4:1
antara file-size dan row-group), sehingga **desain eksperimen tidak berubah**
— hanya skalanya menyesuaikan ukuran tabel. Yang dilarang adalah memaksakan
grid utama pada tabel yang terlalu kecil, karena baseline 128 MiB kemudian
hanya terdiri dari beberapa file dan RQ1 menjadi tidak terjawab.

Keputusan grid dicatat di `configs/layout.yaml: grid_decision` sebelum E3 dan
tidak boleh diubah setelah melihat hasil latency. Implementasi aturan ini ada
di `src/inspect_parquet.py` (`projected_file_count`, `grid_is_feasible`) dan
diuji di `tests/test_file_size_separation.py`.

Jika bahkan fallback grid tidak layak, opsi yang sah adalah memakai
`Dataset_AIS_SPEC.parquet` (13,5 juta baris, lebih banyak kolom string) sebagai
tabel utama dan AIS_POS sebagai sekunder. Menggandakan baris secara sintetis
**bukan** opsi — itu menghapus alasan memakai dataset nyata.

---

### Faktor B — Measured Query Selectivity

Target awal:

```text
0.01%
0.1%
1%
5%
10%
50%
```

Optional full-scan control:

```text
100%
```

Definisi:

```text
selectivity(q)
=
N_match(q) / N_total
```

Analisis memakai **measured selectivity**, bukan hanya label target.

#### Sizing awal band pada MMDEC

Periode observasi MMDEC adalah 92 hari (1 Juli – 30 September 2023) dengan
19.014.229 baris. Andai arrival rate seragam, lebar window `Date` per band
adalah:

| Target | Perkiraan baris | Lebar window `Date` |
|---:|---:|---|
| 0,01 % | ~1.901 | ~13 menit |
| 0,1 % | ~19.014 | ~2,2 jam |
| 1 % | ~190.142 | ~22 jam |
| 5 % | ~950.711 | ~4,6 hari |
| 10 % | ~1.901.423 | ~9,2 hari |
| 50 % | ~9.507.114 | ~46 hari |

Dua hal yang harus dibaca dari tabel ini:

1. Band terendah tetap masuk akal — ~1,9k baris pada window ~13 menit cukup
   kecil untuk menguji skipping tanpa menjadi query kosong.
2. Angka-angka ini **hanya titik awal pencarian**. Trafik AIS tidak seragam
   (artikel MMDEC, Fig. 5 menunjukkan variasi mingguan), sehingga boundary
   final ditentukan oleh `COUNT(*)` aktual, bukan aritmetika di atas. Jalankan
   `sql/calibration/rows_per_day.sql` lebih dulu untuk melihat distribusi
   harian sebelum menempatkan window.

Band diterima bila `|measured - target| / target <= 0,20` dan urutan measured
selectivity monoton naik (`configs/selectivity.yaml`, diuji di
`tests/test_selectivity.py`).

---

## Query Families

### Q1 — Predicate Scan

```sql
SELECT COUNT(*)
FROM table
WHERE Date BETWEEN start_ts AND end_ts;
```

Tujuan:
- scan/pruning;
- output kecil;
- minimal result-transfer confound.

### Q2 — Selective Aggregate

```sql
SELECT AVG(SpeedOverGround), MAX(SpeedOverGround)
FROM table
WHERE Date BETWEEN start_ts AND end_ts;
```

Tujuan:
- scan;
- decompression;
- value processing.

### Q3 — Selective Group-By

```sql
SELECT MessageType, COUNT(*), AVG(SpeedOverGround)
FROM table
WHERE Date BETWEEN start_ts AND end_ts
GROUP BY MessageType;
```

Tujuan:
- scan;
- aggregation ringan;
- sedikit additional compute.

`MessageType` pada AIS_POS hanya bernilai 1, 2, 3, 18, 19, atau 27 (artikel
MMDEC), sehingga Q3 menghasilkan **maksimal 6 grup**. Kardinalitas rendah ini
sesuai tujuan Q3 dan harus dinyatakan di manuskrip agar Q3 tidak salah dibaca
sebagai uji tekanan hash aggregation.

### Q4 — Entity Robustness

```sql
SELECT COUNT(*)
FROM table
WHERE Mmsi IN (...);
```

Predikat pada `Mmsi` tidak selaras dengan row order (yang Date-clustered),
sehingga Q4 menguji perilaku ketika file-level skipping tidak membantu.
Sampel MMSI diambil dari 25.130 MMSI unik, dibekukan sekali
(`sql/calibration/mmsi_sample.sql`), dan literalnya identik di seluruh variant.

Q4 bukan bagian main factorial grid.

---

## Variabel yang Harus Dibekukan

### Row-Group Target

Target awal:

```text
32 MiB
```

Harus sama pada 32/64/128/256 MiB data-file variants.

Ini adalah kontrol konstruk utama.

### Row Order

Main:

```text
Date-clustered / fixed order
```

Robustness:

```text
deterministic shuffled
atau original order
```

### Partitioning

Main study:

```text
unpartitioned
```

Jangan menambah partitioning sebagai faktor.

### Compression

Gunakan:

```text
Snappy
```

Writer version dan encoding settings sama.

### Query Engine

Main:

```text
Trino
```

### Hardware

Target awal:

```text
8 vCPU
16 GB RAM
local SSD
Docker Compose
```

Angka aktual boleh berubah, tetapi harus dibekukan sebelum main run.

---

## Resource-Constrained Definition

Istilah “resource-constrained” harus dapat direplikasi.

Catat:
- CPU model;
- cores/threads;
- RAM;
- storage medium;
- filesystem;
- OS;
- kernel;
- Docker version;
- Java version;
- Trino version;
- Spark version;
- Iceberg version;
- MinIO version;
- MinIO dan Trino colocated atau tidak;
- resource caps;
- concurrency.

Autoscaling tidak digunakan.

Main latency benchmark memakai satu query stream.

---

## Data-File Size ≠ Row-Group Size

Parquet memiliki beberapa level physical organization:

```text
file
  └── row groups
       └── pages
```

Jika target file size dan row-group size berubah bersamaan, penelitian menjadi confounded.

Contoh yang **tidak boleh**:

```text
32 MiB file  → 8 MiB row group
64 MiB file  → 16 MiB row group
128 MiB file → 32 MiB row group
256 MiB file → 64 MiB row group
```

Desain yang benar:

```text
32 MiB file  → 32 MiB target row group
64 MiB file  → 32 MiB target row group
128 MiB file → 32 MiB target row group
256 MiB file → 32 MiB target row group
```

Realized row-group size tetap harus diverifikasi.

---

## Mengapa File Kecil Bisa Membantu?

Kemungkinan mekanisme:
- file min/max statistics lebih sempit;
- lebih banyak file dapat di-skip;
- low-selectivity query membaca lebih sedikit data;
- lebih banyak split dapat meningkatkan parallelism sampai titik tertentu.

---

## Mengapa File Kecil Bisa Merugikan?

Kemungkinan overhead:
- metadata;
- listing;
- manifest lookup;
- file open;
- object GET;
- split scheduling;
- task scheduling;
- writer overhead;
- compaction/rewrite cost.

Pada environment kecil, overhead split dapat menjadi dominan.

---

## Mengapa Crossover Mungkin Ada?

Secara konseptual:

```text
selectivity rendah
→ skipping lebih penting
→ file lebih kecil mungkin membantu
```

ketika selectivity naik:

```text
lebih banyak file dibaca
→ skipping advantage mengecil
→ many-file overhead makin penting
```

Tetapi crossover:
- tidak dijamin;
- tidak boleh dipaksakan;
- bisa hilang jika row-order tidak selaras dengan predicate;
- bisa lemah jika row-group pruning lebih dominan daripada file-level effect.

---

## Layout Generation

Semua variants harus berasal dari snapshot yang sama.

Yang boleh berubah:

```text
target data-file size
```

Yang harus tetap sama:
- row values;
- schema;
- row count;
- row order;
- row-group target;
- compression;
- partitioning;
- writer version;
- encoding settings.

---

## Realized File-Size Validation

Target file size bukan ground truth.

Setelah write:
- hitung file count;
- median size;
- IQR;
- min;
- max;
- coefficient of variation;
- row-groups/file;
- median row-group size.

Jika actual file-size distributions terlalu overlap:

```text
STOP MAIN EXPERIMENT
```

Perbaiki layout writer dahulu.

---

## Semantic Equivalence

Semua variants harus menghasilkan semantics yang sama.

Minimal:
- row count sama;
- schema sama;
- checksum/invariant sama;
- Q1/Q2/Q3 result sama.

Contoh:

```text
COUNT(*)_32
=
COUNT(*)_64
=
COUNT(*)_128
=
COUNT(*)_256
```

---

## Selectivity Calibration

Gunakan `Date`.

Alur:

```text
canonical table
    ↓
candidate Date window
    ↓
COUNT matched rows
    ↓
measured selectivity
    ↓
adjust if necessary
    ↓
freeze boundary
```

Simpan ke:

```text
data/manifests/selectivity_manifest.csv
```

Setelah freeze, jangan mengubah boundary berdasarkan hasil latency.

---

## Main Factorial Grid

Primary:

```text
4 file sizes
×
6 selectivity bands
×
3 query families
=
72 conditions
```

Per condition:

```text
2 warm-up
+
>=20 measured repetitions
```

Minimum measured runs:

```text
72 × 20
=
1,440 measured query runs
```

Karena itu scope harus dijaga.

---

## Warm-Up dan Cache

Main study:

```text
consistent warm-up
→ steady-state measured runs
```

Warm-up:
- dicatat;
- diberi label;
- tidak masuk primary analysis.

Jangan campur cold dan warm runs tanpa label.

---

## Run Randomization

Jangan jalankan:

```text
semua 32 MiB
lalu semua 64 MiB
lalu semua 128 MiB
lalu semua 256 MiB
```

Gunakan block-randomized order dengan seed.

Tujuannya mengurangi:
- thermal drift;
- JVM stabilization;
- cache drift;
- background load bias;
- time-of-day bias.

---

## Raw Run Schema

Minimal per query run:

```json
{
  "run_id": "...",
  "block_id": "...",
  "seed": 42,
  "warmup": false,
  "file_size_target_mib": 128,
  "file_size_variant": "ais_pos_128",
  "query_family": "Q2",
  "query_id": "Q2_S005",
  "target_selectivity": 0.05,
  "measured_selectivity": 0.0487,
  "start_ts": "...",
  "end_ts": "...",
  "trino_query_id": "...",
  "latency_ms": 812.4,
  "physical_input_bytes": 123456789,
  "processed_input_rows": 912345,
  "processed_input_bytes": 156789123,
  "completed_splits": 18,
  "cpu_ms": 604.0,
  "peak_memory_bytes": 251658240,
  "planning_ms": 25.0,
  "status": "FINISHED",
  "retry": false
}
```

Raw logs tidak boleh hanya menyimpan aggregate.

---

## Telemetry

### Query Level

- latency;
- physical input bytes;
- processed rows;
- processed bytes;
- completed splits;
- CPU time;
- peak memory;
- planning time;
- status;
- errors/retries.

### Host Level

- CPU utilization;
- memory;
- disk I/O;
- network I/O;
- timestamp.

### Important Naming Rule

Jangan menyamakan:

```text
split count == file count
```

atau:

```text
physical input bytes == network bytes
```

tanpa verifikasi.

---

## Metrik Primer

1. p50 end-to-end query latency.
2. p95 latency jika repetitions cukup.
3. paired latency difference.
4. latency ratio terhadap 128 MiB.

---

## Metrik Mekanisme

- physical input bytes;
- processed input rows;
- processed input bytes;
- completed splits;
- file/object access bila observable;
- CPU time;
- CPU utilization;
- peak memory;
- planning/scheduling time.

---

## Write/Maintenance Guardrail

- layout-build wall time;
- write throughput;
- generated file count;
- rewrite/compaction time;
- storage footprint.

Write cost bukan faktor utama RQ1, tetapi harus muncul sebagai guardrail.

---

## Definisi Crossover

Untuk file-size conditions `a` dan `b` pada selectivity `s`:

```text
Delta(a,b,s)
=
median[
  latency_a(q,s)
  -
  latency_b(q,s)
]
```

Interpretasi:

```text
Delta < 0 → a lebih cepat
Delta > 0 → b lebih cepat
```

Crossover region hanya boleh dinyatakan bila:

1. tanda berubah antara selectivity bands bertetangga atau fitted interaction;
2. perubahan cukup stabil;
3. bootstrap 95% CI memberi evidence yang memadai;
4. arah direplikasi pada query family utama;
5. bukan akibat satu outlier atau satu literal query.

Jika CI lebar:

```text
crossover region uncertain
```

Jika tidak ada sign change:

```text
no crossover in tested range
```

---

## Analisis Statistik

Latency cenderung right-skewed.

Laporkan:
- p50;
- p95;
- IQR;
- bootstrap 95% CI.

Gunakan paired design karena query instance yang sama dijalankan di seluruh file-size variants.

### Paired Analysis

Gunakan:
- paired difference;
- paired ratio;
- paired bootstrap.

### Confirmatory Interaction

Bila memungkinkan:

```text
log_latency
~
file_size
*
measured_selectivity
+
query_family
+
random effect for paired run/query block
```

Jika mixed-effects terlalu kompleks:
- permutation interaction test;
- effect size;
- CI.

### Multiple Comparisons

Gunakan Holm correction bila banyak pairwise tests.

### Unit Analisis

Bukan jumlah row.

Unit analisis performance:
- benchmark run;
- query instance;
- paired block.

---

## Eksperimen E0 — Data & Environment Sanity

- download MMDEC dari DOI `10.5281/zenodo.17491518`;
- simpan DOI/source/lisensi;
- checksum;
- verifikasi row count 19.014.229 dan 25.130 MMSI unik;
- verifikasi 14 kolom Tabel 2 dan tipe temporal `Date`;
- verifikasi rentang tanggal 1 Juli – 30 September 2023;
- **ukur ukuran tabel kanonik** (menentukan grid di E1);
- deploy MinIO + Iceberg REST catalog + Trino;
- smoke query;
- ukur noise floor;
- freeze hardware/software/cap resource.

Gate:

```text
source valid terhadap artikel MMDEC
row count, MMSI, kolom, tipe Date valid
ukuran tabel kanonik terukur
lakehouse smoke test OK
resource caps + versi image frozen
noise floor terukur
```

---

## Eksperimen E1 — Controlled Layout Generation

Pilih grid lebih dulu berdasarkan ukuran tabel kanonik dari E0:

```text
kondisi terbesar >= 8 file  -> grid utama    32 | 64 | 128 | 256 MiB   (row-group 32 MiB)
kondisi terbesar <  8 file  -> grid fallback  8 | 16 |  32 |  64 MiB   (row-group  8 MiB)
```

Catat keputusannya di `configs/layout.yaml: grid_decision` sebelum menulis
variant apa pun. Lalu buat keempat layout dari canonical snapshot yang sama.

Verifikasi:
- actual file size distribution;
- file count;
- row groups/file;
- realized row-group size;
- row count;
- schema;
- checksum/invariants;
- result equivalence.

Ukur:
- layout build time;
- write throughput.

---

## Eksperimen E2 — Selectivity Calibration

Urutannya penting, karena trafik AIS tidak seragam:

1. jalankan `sql/calibration/date_bounds.sql` — pastikan rentang 92 hari utuh;
2. jalankan `sql/calibration/rows_per_day.sql` — lihat distribusi harian aktual;
3. tempatkan kandidat window per band memakai distribusi itu, dengan tabel
   sizing seragam hanya sebagai titik awal;
4. `COUNT(*)` per kandidat, hitung measured selectivity;
5. terima band bila |measured - target| / target <= 0,20;
6. pastikan measured selectivity monoton naik antar-band;
7. bekukan boundary, literal, dan query template.

Band:

```text
0.01% | 0.1% | 1% | 5% | 10% | 50%
```

Setelah dibekukan, boundary tidak boleh disesuaikan berdasarkan hasil latency.

---

## Eksperimen E3 — Main Factorial Benchmark

Untuk setiap:

```text
file-size × selectivity × Q1-Q3
```

lakukan:
- 2 warm-up;
- >=20 measured repetitions;
- block-randomized order;
- raw Trino telemetry;
- host telemetry;
- failed run logging.

Jangan tuning protocol dari bentuk preliminary results.

---

## Eksperimen E4 — Mechanism & Failure Analysis

Hubungkan latency dengan:
- physical input;
- split count;
- CPU;
- memory;
- planning;
- object access bila tersedia.

Klasifikasikan:
- pruning wins;
- file/split overhead wins;
- resource saturation;
- cache/warm-up instability;
- unexplained.

Audit minimal 15 abnormal run/query cases.

---

## Eksperimen E5 — Robustness

### Row-Order Control

Ulang subset representatif pada:

```text
deterministic shuffled order
```

Tujuan:
mengetahui apakah efek utama sangat tergantung pada Date clustering.

### Secondary Table

Opsional:
- `Dataset_AIS_SPEC.parquet` (13.558.007 baris, 23.958 MMSI unik);
- `Dataset_BATHYMETRY.parquet` (12.386.244 baris).

Secondary validation baru dilakukan setelah main result complete.

---

## Eksperimen E6 — Mixed Workload Decision Map

Article extension.

Buat satu atau dua held-out traces.

Bandingkan:

```text
selectivity-aware chosen size
vs
fixed 128 MiB
vs
retrospective best fixed size
```

Laporkan:
- total workload latency;
- regret;
- write-cost guardrail.

Jangan menyebutnya online adaptation.

---

## Quality Gates Sebelum Main Experiment

### G1 — Data
- [ ] AIS_POS row count = 19.014.229 (artikel MMDEC).
- [ ] MMSI unik = 25.130.
- [ ] 14 kolom Tabel 2 artikel hadir; kolom tambahan didokumentasikan.
- [ ] `Date` bertipe temporal, bukan string.
- [ ] rentang `Date` mencakup 1 Juli – 30 September 2023.
- [ ] ukuran tabel kanonik terukur (input keputusan grid).
- [ ] source manifest + DOI tersedia.
- [ ] checksum tersedia.

Diperiksa oleh `src/validate_source.py`.

### G2 — Semantic Equivalence
- [ ] query results identik antar-layout.

### G3 — File-Size Separation & Kelayakan Grid
- [ ] kondisi file-size terbesar menghasilkan >= 8 file (idealnya >= 16).
- [ ] grid yang dipakai (utama atau fallback) tercatat di
      `configs/layout.yaml: grid_decision` beserta alasannya.
- [ ] realized distributions cukup terpisah: IQR antar-kondisi bertetangga
      tidak bertumpuk dan rasio median >= 1,5.

Diperiksa oleh `src/inspect_parquet.py`
(`grid_is_feasible`, `file_size_separation`).

### G4 — Row-Group Control
- [ ] target row group sama di seluruh variant.
- [ ] realized median row-group menyebar <= 25 % antar-variant.
- [ ] tipe nested `id_chunk` terpelihara setelah rewrite.

Diperiksa oleh `src/inspect_parquet.py` (`row_group_control`).

### G5 — Selectivity
- [ ] boundary ditetapkan dari distribusi harian aktual, bukan asumsi rate seragam.
- [ ] setiap band memenuhi |measured - target| / target <= 0,20.
- [ ] measured selectivity monoton naik antar-band.
- [ ] measured values disimpan dan boundary dibekukan sebelum benchmark.

### G6 — Observability
- [ ] latency tersedia.
- [ ] physical input tersedia.
- [ ] split metrics tersedia.
- [ ] CPU/memory tersedia.
- [ ] `missing_metrics` kosong pada dry-run H8 — telemetry yang diam-diam
      kosong adalah mode kegagalan yang sudah pernah terjadi pada harness ini.

### G7 — Resource Freeze
- [ ] hardware frozen.
- [ ] seluruh image di-pin ke tag eksplisit (bukan `latest`) dan versinya
      disalin ke `data/manifests/environment_snapshot.yaml`.
- [ ] cap CPU/memory ditegakkan lewat `deploy.resources.limits` + `.env`.
- [ ] concurrency frozen (satu query stream).
- [ ] noise floor terukur; perbedaan di bawahnya tidak ditafsirkan.

### G8 — Baseline
- [ ] 128 MiB baseline berjalan stabil.

### G9 — Claim Freeze
- [ ] crossover criterion sudah ditulis.
- [ ] primary metrics sudah ditulis.
- [ ] query templates sudah frozen.

Main benchmark hanya dimulai jika G1–G9 lulus.

---

## Failure Analysis

Minimal categories:
1. latency outlier;
2. unexpected physical input;
3. split explosion;
4. CPU saturation;
5. memory pressure;
6. cache instability;
7. semantic mismatch;
8. writer target miss;
9. row-group confound;
10. missing telemetry;
11. retry/error;
12. anomalous query plan.

Failed runs tetap disimpan.

---

## Grafik dan Tabel Wajib

1. MMDEC source/snapshot manifest.
2. Target vs realized file-size table.
3. Row-group distribution table.
4. p50 latency heatmap.
5. p50 latency vs measured selectivity plot.
6. p95 latency vs measured selectivity plot.
7. latency ratio vs 128 MiB.
8. physical input bytes vs selectivity.
9. completed splits vs selectivity.
10. crossover paired-difference plot + 95% CI.
11. write/layout-build time.
12. generated file count.
13. ordered vs shuffled robustness plot.
14. failure-analysis table.
15. optional held-out workload regret figure.

---

## Threats to Validity

### Construct Validity

File size dapat tertukar dengan:
- row-group size;
- sorting;
- partitioning;
- compression;
- writer behavior;
- split sizing.

Karena itu physical metadata wajib dilaporkan.

### Internal Validity

Ancaman:
- cache;
- JVM warm-up;
- background load;
- thermal throttling;
- object-store locality;
- run order.

Mitigasi:
- warm-up;
- randomization;
- repeated runs;
- dedicated benchmark window.

### Statistical Validity

p95 tidak stabil dengan repetitions sedikit.

Jangan menginterpretasikan perbedaan kecil yang masih berada dalam noise floor.

### External Validity

Klaim dibatasi pada:
- MMDEC;
- Trino;
- Iceberg;
- MinIO;
- tested resource budget.

Jangan langsung diperluas ke:
- BigQuery;
- Snowflake;
- remote AWS S3;
- engine lain.

### Scale Validity

Tabel kanonik AIS_POS berada pada skala ratusan MiB sampai beberapa GiB, bukan
puluhan TiB. Konsekuensinya:

- jumlah file per kondisi kecil, sehingga varians antar-run lebih terasa;
- efek metadata dan planning proporsional lebih besar daripada pada tabel besar;
- grid file-size dibatasi oleh ukuran tabel, bukan dipilih bebas.

Klaim harus menyebut skala tabel yang diuji. Ekstrapolasi ke tabel jauh lebih
besar tidak dibenarkan oleh data ini.

### Dataset-Order Validity

Date clustering dapat memperbesar min/max skipping benefit.

Row-order robustness penting.

### Instrumentation Validity

Split bukan file.
Physical input bukan network bytes.

---

## Quality Gate — Minimum Skripsi

- [ ] AIS_POS snapshot terdokumentasi (DOI, tanggal unduh, lisensi).
- [ ] source checksum tersedia.
- [ ] row count, MMSI unik, kolom, dan tipe `Date` terverifikasi terhadap artikel MMDEC.
- [ ] keputusan grid (utama/fallback) tercatat beserta ukuran tabel kanonik.
- [ ] empat layout valid dan jumlah file pada kondisi terbesar >= 8.
- [ ] semantic equivalence valid.
- [ ] row-group fixed.
- [ ] compression fixed.
- [ ] row order fixed.
- [ ] unpartitioned fixed.
- [ ] engine frozen.
- [ ] hardware frozen.
- [ ] minimal 5 selectivity levels.
- [ ] Q1-Q3 selesai.
- [ ] >=20 measured repetitions per main condition atau nilai pilot yang dibenarkan.
- [ ] p50/p95 tersedia.
- [ ] physical input tersedia.
- [ ] split telemetry tersedia.
- [ ] CPU/memory tersedia.
- [ ] write guardrail tersedia.
- [ ] paired analysis selesai.
- [ ] crossover criterion tidak diubah post-hoc.
- [ ] failure analysis selesai.
- [ ] noise floor dilaporkan dan dipakai saat menafsirkan perbedaan kecil.
- [ ] fresh reproduction berhasil.

---

## Quality Gate — Artikel

- [ ] seluruh minimum skripsi selesai;
- [ ] row-order robustness selesai;
- [ ] secondary-table subset selesai atau ada alasan kuat;
- [ ] interaction analysis selesai;
- [ ] bootstrap CI lengkap;
- [ ] actual file-size metadata dipublikasikan;
- [ ] artikel data MMDEC disitasi (DOI 10.1016/j.dib.2026.112629) dan DOI
      dataset dicantumkan (10.5281/zenodo.17491518);
- [ ] row-group metadata dipublikasikan;
- [ ] query catalog tersedia;
- [ ] raw-results schema tersedia;
- [ ] final literature verification selesai;
- [ ] tidak memakai “optimal universal”;
- [ ] tidak memakai “first study” tanpa bukti;
- [ ] held-out trace bebas leakage bila E6 dipakai.

---

## Hal yang Tidak Dikerjakan pada Bulan Pertama

Jangan menambahkan:
- partition evolution;
- adaptive compaction algorithm;
- multiple row-group sizes;
- multiple codecs;
- multi-engine shootout;
- distributed scaling;
- spatial query optimization;
- remote-cloud cost benchmark;
- dashboard;
- UI;
- ML recommender;
- online adaptive tuning.

Semua dapat menjadi future work.

---

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
- bekukan RQ1–RQ5, hipotesis H1–H5, dan novelty boundary;
- unduh MMDEC dari DOI `10.5281/zenodo.17491518`, catat tanggal dan lisensi;
- hitung sha256, isi `data/manifests/source_manifest.csv`.
- Deliverable: source manifest terisi.

**H2 — Validasi sumber terhadap artikel**
- jalankan `src/validate_source.py`: row count 19.014.229, MMSI unik 25.130,
  14 kolom Tabel 2, tipe `Date` temporal;
- EDA distribusi baris per hari (`sql/calibration/rows_per_day.sql` setelah
  tabel terdaftar, atau PyArrow sebelum itu);
- **ukur ukuran tabel kanonik** — ini input keputusan grid di H5.
- Deliverable: laporan validasi + ukuran tabel. Gate: **G1**.

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

### Minggu 2 — Main Factorial Benchmark (E3)

Anggaran waktu satu pass penuh:

```text
72 kondisi x (2 warm-up + 20 measured) = 1.584 eksekusi
durasi pass = 1.584 x (latency rata-rata + overhead harness)
```

Isi angka ini dari pilot H7. Jika satu pass > 12 jam, kurangi dulu band
opsional atau repetisi p95 — jangan kurangi jumlah kondisi grid utama.

**H8 — Dry-run harness**
- jalankan satu blok penuh (~10 % beban) end-to-end;
- verifikasi setiap raw run punya latency, physical input, splits, CPU, memory
  (`missing_metrics` harus kosong);
- verifikasi schema JSONL sesuai `results/README.md`;
- perbaiki instrumentasi sebelum melanjutkan.
- Deliverable: dry-run bersih. Gate: **G6 dikonfirmasi pada data nyata**.

**H9–H11 — Pass utama**
- 72 kondisi x (2 warm-up + >= 20 measured), block-randomized dengan seed;
- satu query stream, tanpa beban lain di host;
- simpan run gagal apa adanya;
- catat setiap pass ke `data/manifests/run_index.csv`.
- Deliverable: >= 1.440 measured run.

**H12 — Repetisi tambahan**
- tambah repetisi menuju 30 pada kondisi ber-CV tinggi, untuk klaim p95;
- ulangi kondisi yang gagal atau telemetry-nya tidak lengkap.

**H13 — Buffer + run di luar grid**
- hari buffer untuk keterlambatan Minggu 1–2;
- jika lancar: Q4 entity robustness dan full-scan control 100 % (opsional).

**H14 — Integrity check dan freeze raw**
- periksa kelengkapan run per kondisi, telemetry hilang, retry;
- periksa drift antar-hari (bandingkan blok baseline H9 vs H11);
- bekukan `results/raw` sebagai raw v1.
- Deliverable: raw dataset v1 beku.

---

### Minggu 3 — Analisis, Mekanisme, Robustness

**H15 — Agregasi**
- raw JSONL -> tabel processed;
- p50, p95, IQR, bootstrap 95 % CI per kondisi;
- kecualikan warm-up, pertahankan label run gagal.

**H16 — Analisis berpasangan**
- paired difference dan ratio terhadap baseline;
- heatmap p50; plot latency vs measured selectivity (p50 dan p95).
- Deliverable: figure 4–7 dari daftar wajib.

**H17 — Deteksi crossover**
- terapkan criterion yang sudah dibekukan di H1/H7 tanpa perubahan;
- laporkan salah satu dari: crossover, uncertain region, atau no crossover.
- Deliverable: figure 10.
- Aturan: hasil "tidak ada crossover" ditulis sebagai temuan, bukan kegagalan.

**H18 — Mechanism attribution (E4)**
- hubungkan latency dengan physical input, splits, CPU, memory, planning;
- klasifikasikan tiap regime: pruning win, split/overhead win, saturasi,
  instabilitas cache, atau unexplained.
- Deliverable: figure 8–9.

**H19 — Failure analysis (E4)**
- audit >= 15 kasus abnormal menurut 12 kategori;
- pastikan tidak ada kategori yang menampung semuanya sebagai "unexplained".
- Deliverable: figure/tabel 14.

**H20 — Robustness row-order (E5)**
- bangun variant `deterministic_shuffled`, jalankan subset representatif;
- bandingkan dengan hasil Date-clustered.
- Deliverable: figure 13.
- Ini yang memisahkan efek file-size dari efek min/max alignment; jangan
  dilewati kecuali ditulis alasannya.

**H21 — Write guardrail dan freeze results v1**
- rangkum biaya layout-build, file count, footprint, compaction (RQ4);
- periksa daftar 15 figure/tabel wajib, tandai yang belum ada;
- bekukan results v1.
- Deliverable: figure 11–12 + results v1.

---

### Minggu 4 — Reproduksi, Ekstensi, Manuskrip

**H22 — Reproduksi bersih**
- teardown penuh, redeploy dari `.env` + compose, muat ulang canonical
  snapshot, jalankan ulang subset;
- bandingkan dengan results v1 dan laporkan selisihnya.
- Deliverable: laporan reproduksi.
- Ini butir wajib pada quality gate minimum skripsi.

**H23 — Secondary table (E5, opsional)**
- subset kondisi pada `Dataset_AIS_SPEC.parquet` atau
  `Dataset_BATHYMETRY.parquet`;
- jika dilewati, tulis alasannya di Threats to Validity.

**H24 — Mixed workload decision map (E6, opsional/artikel)**
- 1–2 held-out trace, bebas leakage dari data kalibrasi;
- bandingkan selectivity-aware vs fixed baseline vs retrospective best;
- laporkan total latency, regret, dan write guardrail.
- Deliverable: figure 15. Jangan menyebutnya online adaptation.

**H25 — Verifikasi literatur final**
- cek klaim kebaruan; hapus "optimal universal" dan "first study" tanpa bukti.
- Deliverable: Related Work.

**H26 — Tulis Methods**
- Dataset & Testbed, Experimental Design, seluruh nilai beku dan versi.

**H27 — Tulis Results**
- Results RQ1/RQ2, Mechanism RQ3, Write trade-off RQ4, Robustness RQ5,
  Threats to Validity.

**H28 — Tulis penutup dan rilis artifact**
- Discussion, Conclusion, Abstract;
- dokumentasi artifact: manifest, config, query catalog, schema raw results;
- periksa Quality Gate Minimum Skripsi dan Quality Gate Artikel butir demi butir.
- Deliverable: manuscript v0.8–v1.0.

---

### Jalur Minimum Bila Tertinggal

Urutan pemotongan, dari yang paling boleh dikorbankan:

```text
1. E6 mixed workload decision map (H24)
2. secondary table (H23)
3. kondisi opsional 512 MiB dan full-scan 100%
4. repetisi 30 untuk klaim p95  -> cukup 20, dan p95 tidak diklaim
5. band selectivity dari 6 -> 5
```

Yang **tidak boleh** dikorbankan, karena masing-masing membatalkan RQ atau
validitas: verifikasi sumber (H2), keputusan grid berbasis ukuran tabel (H5),
semantic equivalence (H6), kontrol row-group (H6), freeze selectivity sebelum
benchmark (H7), >= 20 repetisi pada grid utama (H9–H12), robustness row-order
(H20), dan reproduksi bersih (H22).

---

## Struktur Repository

```text
dsic-2604/
├── README.md
├── pyproject.toml
├── Makefile
├── .gitignore
├── .env.example
├── configs/
│   ├── environment.yaml          # host, cap resource, image ter-pin, katalog
│   ├── layout.yaml               # grid file-size, aturan kelayakan, invariant
│   ├── selectivity.yaml          # band, toleransi, konteks periode MMDEC
│   ├── benchmark.yaml            # repetisi, randomisasi, metrik, run di luar grid
│   └── crossover.yaml            # criterion beku
├── infra/
│   ├── docker-compose.yml        # MinIO + mc init + Iceberg REST + Trino + Spark
│   ├── trino/catalog/iceberg.properties
│   ├── minio/README.md
│   └── spark/README.md
├── data/
│   ├── README.md
│   ├── checksums/
│   └── manifests/
│       ├── source_manifest_template.csv
│       ├── layout_manifest_template.csv
│       ├── selectivity_manifest_template.csv
│       ├── write_cost_manifest_template.csv
│       ├── run_index_template.csv
│       └── environment_snapshot_template.yaml
├── sql/
│   ├── smoke.sql
│   ├── calibration/
│   │   ├── count_total.sql
│   │   ├── count_range.sql
│   │   ├── date_bounds.sql            # verifikasi periode 92 hari
│   │   ├── rows_per_day.sql           # distribusi harian sebelum sizing band
│   │   ├── message_type_profile.sql   # kardinalitas GROUP BY Q3
│   │   └── mmsi_sample.sql            # sampel entity beku untuk Q4
│   └── queries/
│       ├── Q1_predicate_scan.sql
│       ├── Q2_selective_aggregate.sql
│       ├── Q3_selective_groupby.sql
│       └── Q4_entity_robustness.sql
├── src/
│   ├── common.py
│   ├── mmdec.py                  # kontrak angka & kolom dari artikel MMDEC
│   ├── validate_source.py        # G1: row count, MMSI, kolom, tipe Date
│   ├── inspect_parquet.py        # G3/G4: separasi file-size, kontrol row-group
│   ├── generate_layouts.py
│   ├── calibrate_selectivity.py  # G5: measured selectivity + audit band
│   ├── benchmark.py
│   ├── collect_trino_stats.py    # G6: normalisasi telemetry Trino
│   ├── collect_system_metrics.py
│   ├── validate_equivalence.py   # G2
│   ├── analyze_latency.py
│   ├── detect_crossover.py
│   └── failure_analysis.py
├── tests/
│   ├── test_source_contract.py
│   ├── test_selectivity.py
│   ├── test_semantic_equivalence.py
│   ├── test_file_size_separation.py
│   ├── test_crossover.py
│   └── test_run_randomization.py
├── scripts/
│   ├── run_smoke.sh
│   ├── build_layouts.sh
│   ├── calibrate_selectivity.sh
│   ├── run_main_benchmark.sh
│   └── analyze_results.sh
├── results/
│   ├── README.md                 # schema raw run + aturan instrumentasi
│   ├── raw/
│   ├── processed/
│   ├── figures/
│   └── tables/
├── refs/
│   ├── README.md                 # sitasi + kontrak verifikasi MMDEC
│   └── 1-s2.0-S2352340926001824-main.pdf
└── paper/
    └── manuscript.md
```

Direktori yang dibuat saat berjalan dan diabaikan Git: `data/raw/`,
`data/canonical/`, `data/layouts/`, `infra/volumes/`, isi `results/*`.

---

## Setup Minimum

### Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Environment

```bash
cp .env.example .env
# isi MINIO_ROOT_PASSWORD dan cap resource sebelum menjalankan apa pun
```

`.env` tidak boleh di-commit. Cap resource di `.env` adalah definisi
operasional "resource-constrained" dan ikut dibekukan oleh G7.

### Infrastructure

```bash
docker compose -f infra/docker-compose.yml --env-file .env up -d
docker compose -f infra/docker-compose.yml --env-file .env ps
```

Urutan start: MinIO -> `minio-init` (membuat bucket, lalu keluar) ->
Iceberg REST catalog -> Trino. Spark berada di profil `layout` dan tidak ikut
start default:

```bash
docker compose -f infra/docker-compose.yml --env-file .env --profile layout up -d spark
```

Katalog memakai tipe `rest`, bukan `hadoop`: Trino tidak mendukung katalog
Iceberg berbasis filesystem, dan Spark (writer layout) serta Trino (reader
benchmark) harus melihat metadata tabel yang sama persis.

### Tests

```bash
pytest -q
```

### Smoke

```bash
make smoke
```

Main experiment jangan dijalankan sebelum quality gates lulus.

---

## Tools Penelitian

### Storage / Lakehouse

```text
MinIO
Apache Iceberg (REST catalog, dibagi antara Spark writer dan Trino reader)
Parquet
```

### Query

```text
Trino
```

### Layout Generation

```text
Spark / PySpark
```

### Inspection

```text
PyArrow
Pandas
NumPy
```

### Benchmark Harness

```text
Python
Trino Python client
YAML
JSONL / CSV
```

### Statistics

```text
SciPy
statsmodels
paired bootstrap
permutation test
```

### Visualization

```text
matplotlib
```

### Telemetry

```text
Trino query stats
psutil
Docker/container stats
MinIO access logs if available
```

---

## Catatan Pembimbing

Alur besarnya:

```text
MMDEC AIS_POS
   ↓
verifikasi
row count | schema | checksum
   ↓
canonical snapshot
   ↓
bekukan:
row order
row-group target
compression
partitioning
writer
engine
hardware
   ↓
generate:
32 | 64 | 128 | 256 MiB
   ↓
cek REALIZED file size
   ↓
cek row-group tetap
   ↓
cek semantic equivalence
   ↓
kalibrasi Date ranges
   ↓
0.01% | 0.1% | 1% | 5% | 10% | 50%
   ↓
ukur measured selectivity
   ↓
freeze Q1 | Q2 | Q3
   ↓
2 warm-up
   ↓
>=20 measured repetitions
   ↓
block-randomized order
   ↓
Trino telemetry + host telemetry
   ↓
p50 / p95
bytes / splits
CPU / memory
   ↓
paired comparison vs 128 MiB
   ↓
crossover / no-crossover
   ↓
mechanism analysis
   ↓
row-order robustness
   ↓
write-cost guardrail
   ↓
conditional decision map
```

Secara eksperimen:

1. **Mulai dari satu tabel utama.** Gunakan `Dataset_AIS_POS.parquet`. Jangan memasukkan seluruh komponen MMDEC karena itu tidak menambah validitas RQ.

2. **Verifikasi sumber.** Pastikan row count, schema, checksum, DOI/source, dan snapshot terdokumentasi sebelum rewrite.

3. **Buat canonical snapshot.** Seluruh layout 32/64/128/256 MiB harus berasal dari baris dan urutan yang sama.

4. **Bekukan row order.** Main study memakai Date-clustered/fixed order. Row-order robustness baru dilakukan setelah main result selesai.

5. **Bekukan row-group size.** Ini kontrol terpenting. Kalau row-group ikut berubah, efek file size tidak dapat diisolasi.

6. **Generate empat layout.** 128 MiB adalah baseline. 32, 64, dan 256 MiB adalah candidate conditions.

7. **Audit actual file size.** Jangan percaya target writer. Hitung median, IQR, min, max, CV, file count, dan row groups/file.

8. **Audit semantic equivalence.** Semua layout harus menghasilkan query result yang sama.

9. **Kalibrasi selectivity aktual.** Gunakan Date ranges lalu hitung `matched_rows / total_rows`. Simpan measured selectivity.

10. **Freeze Q1–Q3.** Jangan mengubah query structure setelah melihat latency.

11. **Warm-up konsisten.** Dua warm-up per condition tidak masuk primary analysis.

12. **Lakukan repeated measurement.** Minimum 20 per condition; 30 lebih baik untuk p95.

13. **Randomisasi run order.** Hindari bias JVM/cache/thermal yang mengikuti urutan file size.

14. **Catat telemetry.** Latency saja tidak cukup untuk menjelaskan mekanisme.

15. **Gunakan paired comparison.** Query literal dan repetition block yang sama dibandingkan antar-layout.

16. **Cari interaction, bukan winner universal.** RQ utama adalah apakah keuntungan relatif berubah bersama selectivity.

17. **Crossover harus pre-defined.** Satu sign flip noisy bukan crossover.

18. **No-crossover tetap valid.** Jangan memaksa novelty bergantung pada hasil positif.

19. **Lakukan row-order robustness.** Ini penting untuk membedakan file-size effect dari clustering/min-max alignment.

20. **Write cost hanya guardrail.** Jangan membangun rekomendasi dari read latency saja.

21. **Jaga scope.** Tidak perlu Spark SQL, DuckDB, multiple codec, multiple partitioning, atau adaptive compaction sebelum main grid selesai.

22. **Hasil akhir berupa decision map bersyarat.** Kesimpulan harus selalu menyebut workload, selectivity range, engine, physical controls, dan resource budget yang diuji.

Yang paling penting: penelitian ini bukan **“berapa ukuran file Parquet terbaik?”**, tetapi **“bagaimana ukuran data-file Parquet dan measured query selectivity saling berinteraksi ketika faktor physical layout lain dikontrol, serta mekanisme apa yang menjelaskan perubahan relative performance tersebut?”**
