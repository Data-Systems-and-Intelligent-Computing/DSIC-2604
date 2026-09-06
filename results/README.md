# Results

Direktori ini menyimpan keluaran pengukuran. Isi `raw/`, `processed/`,
`figures/`, dan `tables/` tidak di-commit (lihat `.gitignore`); yang di-commit
hanya manifest dan tabel ringkas yang masuk manuskrip.

```text
results/
├── raw/         # JSONL per query run, apa adanya (termasuk run gagal)
├── processed/   # agregasi p50/p95/IQR, paired difference, bootstrap CI
├── figures/     # 15 figure/tabel wajib (lihat README utama)
└── tables/      # tabel manuskrip
```

## Schema satu raw run (`results/raw/runs.jsonl`)

Satu baris JSON per eksekusi query. Warm-up ikut dicatat dan diberi label,
tetapi tidak masuk primary analysis.

| Field | Tipe | Catatan |
|---|---|---|
| `run_id` | string | unik per eksekusi |
| `block_id` | string | blok randomisasi |
| `seed` | int | seed randomisasi (`configs/benchmark.yaml`) |
| `warmup` | bool | `true` dikecualikan dari primary analysis |
| `file_size_target_mib` | int | kondisi faktor A |
| `file_size_variant` | string | nama tabel Iceberg, mis. `ais_pos_128` |
| `query_family` | string | `Q1` \| `Q2` \| `Q3` (`Q4` di luar grid) |
| `query_id` | string | literal query beku, mis. `Q2_S005` |
| `target_selectivity` | float | label band |
| `measured_selectivity` | float | dipakai untuk analisis |
| `start_ts` / `end_ts` | ISO 8601 | waktu wall-clock |
| `trino_query_id` | string | penghubung ke telemetry engine |
| `latency_ms` | float | metrik primer |
| `physical_input_bytes` | int | **bukan** network bytes |
| `processed_input_rows` | int | |
| `processed_input_bytes` | int | |
| `completed_splits` | int | **bukan** jumlah file |
| `cpu_ms` | float | |
| `peak_memory_bytes` | int | |
| `planning_ms` | float | |
| `status` | string | `FINISHED` \| `FAILED` |
| `retry` | bool | |
| `missing_metrics` | list | terisi bila telemetry tidak lengkap (gate G6) |

Raw log tidak boleh hanya menyimpan agregat. Run gagal tetap disimpan — ia
adalah data untuk failure analysis (E4), bukan sampah.

## Aturan instrumentasi

- `completed_splits` bukan jumlah file.
- `physical_input_bytes` bukan network bytes; klaim I/O object store harus
  bersumber dari MinIO access log.
- Jika `missing_metrics` tidak kosong pada run mana pun, gate G6 belum lulus.
