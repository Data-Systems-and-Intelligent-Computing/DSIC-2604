# Data

## Sumber

MMDEC: Multimodal Maritime Dataset on the English Channel
DOI dataset: <https://doi.org/10.5281/zenodo.17491518>
Artikel data: Averty et al. (2026), *Data in Brief* 65, 112629 —
<https://doi.org/10.1016/j.dib.2026.112629> (lihat `refs/`).

Lisensi artikel CC BY-NC 4.0. Repository ini **tidak** meredistribusi data
MMDEC; hanya manifest, checksum, snapshot schema, metadata layout, kalibrasi
selectivity, dan hasil pengukuran.

## Tabel utama

`Dataset_AIS_POS.parquet` — 19.014.229 position messages, 25.130 MMSI unik,
periode 1 Juli – 30 September 2023 (92 hari), tipe pesan 1/2/3/18/19/27.

Kolom menurut Tabel 2 artikel (14):

```text
Date, Source, MessageType, Mmsi, NavigationStatus, Latitude, Longitude,
PositionAccuracy, CourseOverGroundDegrees, SpeedOverGround, RateOfTurn,
TrueHeadingDegrees, chunk_folder, id_chunk
```

`chunk_folder` dan `id_chunk` adalah kolom hasil kurasi, bukan field AIS asli.
`id_chunk` berisi **daftar** nama chunk dan keduanya dapat NaN. Tipe nested ini
harus dipertahankan saat rewrite layout — mengubahnya mengubah ukuran file dan
melanggar semantic equivalence.

Sentinel "tidak tersedia" pada Tabel 2 yang relevan untuk Q2/Q3:
`CourseOverGroundDegrees` = 511, `TrueHeadingDegrees` = 511,
`RateOfTurn` = ±128. Artikel tidak menyebut sentinel untuk `SpeedOverGround`;
periksa distribusinya saat EDA dan catat keputusannya. Apa pun keputusannya,
perlakuan harus **identik** di keempat layout variant.

## Tabel sekunder (robustness eksternal, E5)

- `Dataset_AIS_SPEC.parquet` — 13.558.007 status messages, 23.958 MMSI unik.
- `Dataset_BATHYMETRY.parquet` — 12.386.244 data points.

1.172 vessel di AIS_POS tidak memiliki status message padanan; relevan bila
robustness melibatkan join, bukan untuk main grid.

## Aturan repository

Jangan commit file Parquet. Simpan:

| Artefak | Template |
|---|---|
| Snapshot sumber + checksum | `manifests/source_manifest_template.csv` |
| Metadata layout realized | `manifests/layout_manifest_template.csv` |
| Boundary selectivity beku | `manifests/selectivity_manifest_template.csv` |
| Snapshot environment | `manifests/environment_snapshot_template.yaml` |
| Biaya write/maintenance | `manifests/write_cost_manifest_template.csv` |
| Indeks pass benchmark | `manifests/run_index_template.csv` |

Direktori kerja lokal yang diabaikan Git: `data/raw/`, `data/canonical/`,
`data/layouts/`.
