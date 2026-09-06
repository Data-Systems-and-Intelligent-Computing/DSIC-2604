# MinIO

S3-compatible object store untuk testbed DSIC-2604.

- Bucket warehouse dibuat otomatis oleh service `minio-init`
  (`${MINIO_BUCKET}`, default `dsic2604`).
- MinIO dan Trino **colocated** pada satu host (lihat
  `configs/environment.yaml: colocated_minio_trino`). Ini bagian dari definisi
  resource-constrained dan wajib dilaporkan, karena menghilangkan latency
  jaringan yang akan muncul pada object store remote.
- Bekukan placement, bucket, versi image, dan resource cap selama main
  experiment (G7).

## Instrumentation validity

`physical_input_bytes` dari Trino **bukan** network bytes. Jika ingin
mengklaim volume I/O ke object store, ambil angkanya dari MinIO access/audit
log, bukan dari statistik query Trino.

Mengaktifkan audit log ke file (opsional, catat jika dipakai):

```bash
mc admin config set local audit_webhook:bench endpoint="http://<collector>:<port>"
```

Setiap perubahan konfigurasi MinIO di tengah eksperimen membatalkan run
sebelumnya. Catat waktu perubahan bila terpaksa dilakukan.
