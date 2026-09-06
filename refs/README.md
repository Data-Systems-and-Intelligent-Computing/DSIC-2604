# Referensi Sumber Data

## Artikel data (wajib disitasi)

Averty, T., Nasios, I., Ray, C., Piliouras, N. (2026).
**MMDEC: Multimodal maritime dataset on the English channel.**
*Data in Brief*, 65, 112629.
DOI: <https://doi.org/10.1016/j.dib.2026.112629>

File lokal: `1-s2.0-S2352340926001824-main.pdf`

## Dataset

**MMDEC: Multimodal Maritime Dataset on the English Channel** (Zenodo)
DOI: <https://doi.org/10.5281/zenodo.17491518>

Lisensi artikel: CC BY-NC 4.0. Periksa lisensi record Zenodo sebelum redistribusi
turunan; repository ini **tidak** mendistribusikan ulang data MMDEC — hanya
manifest, checksum, metadata layout, dan hasil pengukuran.

## Fakta artikel yang dipakai sebagai kontrak verifikasi

| Item | Nilai menurut artikel | Dipakai di |
|---|---|---|
| Periode observasi | 1 Juli – 30 September 2023 (92 hari) | kalibrasi selectivity (E2) |
| Area of interest | Western Celtic Sea, English Channel, sebagian North Sea | dokumentasi konteks |
| `Dataset_AIS_POS.parquet` | 19.014.229 position messages, 25.130 MMSI unik | `src/validate_source.py` (E0) |
| Tipe pesan posisi | 1, 2, 3, 18, 19, 27 | domain `MessageType` untuk Q3 |
| `Dataset_AIS_SPEC.parquet` | 13.558.007 status messages, 23.958 MMSI unik | secondary table (E5) |
| `Dataset_BATHYMETRY.parquet` | 12.386.244 data points | secondary table (E5) |
| Kolom AIS_POS | Tabel 2 artikel (14 kolom) | `src/validate_source.py` |
| `chunk_folder`, `id_chunk` | kolom tambahan hasil kurasi; `id_chunk` berisi *daftar* nama chunk; keduanya dapat NaN | catatan tipe nested saat rewrite layout |
| Vessel tanpa spec message | 1.172 vessel | catatan robustness join (E5) |

Angka-angka ini adalah **acuan verifikasi**, bukan asumsi. Jika snapshot yang
diunduh berbeda, hentikan dan dokumentasikan selisihnya sebelum melanjutkan E1.
