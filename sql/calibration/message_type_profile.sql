-- Profil MessageType. Menurut artikel MMDEC, pesan posisi yang dipertahankan
-- hanya tipe 1, 2, 3, 18, 19, 27 -> Q3 memiliki maksimal 6 grup.
-- Kardinalitas rendah ini disengaja: Q3 menguji agregasi ringan, bukan
-- tekanan pada hash aggregation.
SELECT
  MessageType,
  COUNT(*) AS n
FROM iceberg.dsic2604.ais_pos_128
GROUP BY MessageType
ORDER BY MessageType;
