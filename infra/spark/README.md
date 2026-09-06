# Spark / PySpark — Controlled Layout Generation

Spark hanya dipakai untuk **menulis ulang layout** (32/64/128/256 MiB) dan
inspeksi. Spark **bukan** query engine pembanding; main benchmark memakai Trino.

## Kontrak penulisan

Yang boleh berubah antar-variant hanya **target ukuran data-file**. Semua hal
lain dibekukan (lihat `configs/layout.yaml`):

| Properti | Nilai | Cara mengunci |
|---|---|---|
| target row-group | 32 MiB (atau 8 MiB pada fallback grid) | `write.parquet.row-group-size-bytes` |
| target data-file | 32/64/128/256 MiB | `write.target-file-size-bytes` |
| compression | snappy | `write.parquet.compression-codec` |
| partitioning | unpartitioned | jangan definisikan partition spec |
| row order | Date-clustered fixed | `ORDER BY Date` deterministik + `spark.sql.shuffle.partitions` tetap |
| schema & nilai | identik | tulis dari canonical snapshot yang sama |

Contoh properti tabel Iceberg:

```sql
ALTER TABLE iceberg.dsic2604.ais_pos_128 SET TBLPROPERTIES (
  'write.target-file-size-bytes' = '134217728',
  'write.parquet.row-group-size-bytes' = '33554432',
  'write.parquet.compression-codec' = 'snappy'
);
```

`write.target-file-size-bytes` adalah **target**, bukan jaminan. Realized file
size wajib diaudit dengan `src/inspect_parquet.py` (gate G3/G4).

## Catatan tipe kolom MMDEC

`Dataset_AIS_POS.parquet` memuat `id_chunk` sebagai **daftar** nama chunk dan
`chunk_folder` yang dapat NaN. Keduanya adalah kolom hasil kurasi, bukan field
AIS asli. Saat rewrite:

- pertahankan tipe nested `list<string>` apa adanya — mengubahnya menjadi string
  akan mengubah ukuran file dan melanggar semantic equivalence;
- verifikasi ulang schema setelah setiap penulisan variant.

## Menjalankan

Dua jalur yang sama-sama sah; pilih satu dan bekukan:

**a. Container** (profil `layout`, tidak ikut `up` default):

```bash
docker compose -f infra/docker-compose.yml --env-file .env --profile layout up -d spark
```

**b. PySpark dari venv host**, dengan paket Iceberg + AWS bundle yang versinya
dicatat di `data/manifests/environment_snapshot.yaml`:

```bash
pyspark \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.9.1,org.apache.iceberg:iceberg-aws-bundle:1.9.1 \
  --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.iceberg.type=rest \
  --conf spark.sql.catalog.iceberg.uri=http://localhost:8181 \
  --conf spark.sql.catalog.iceberg.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.iceberg.s3.endpoint=http://localhost:9000 \
  --conf spark.sql.catalog.iceberg.s3.path-style-access=true
```

Versi Spark, Iceberg runtime, dan AWS bundle harus identik untuk keempat
variant. Regenerasi salah satu variant dengan versi berbeda membatalkan
perbandingan.
