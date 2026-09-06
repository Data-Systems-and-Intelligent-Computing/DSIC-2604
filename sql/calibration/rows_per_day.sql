-- Distribusi baris per hari.
-- Trafik AIS tidak seragam sepanjang periode (artikel MMDEC, Fig. 5),
-- sehingga window selectivity TIDAK boleh dihitung dari asumsi rate konstan.
-- Output ini adalah dasar penempatan boundary sebelum COUNT(*) per kandidat.
SELECT
  CAST(Date AS date) AS day,
  COUNT(*)           AS rows_in_day
FROM iceberg.dsic2604.ais_pos_128
GROUP BY CAST(Date AS date)
ORDER BY day;
