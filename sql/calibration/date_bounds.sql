-- Batas sumbu waktu tabel kanonik.
-- Artikel MMDEC menyatakan periode 1 Juli - 30 September 2023 (92 hari).
-- Verifikasi bahwa snapshot benar-benar mencakup rentang tersebut sebelum E2.
SELECT
  MIN(Date) AS min_date,
  MAX(Date) AS max_date,
  COUNT(*)  AS total_rows
FROM iceberg.dsic2604.ais_pos_128;
