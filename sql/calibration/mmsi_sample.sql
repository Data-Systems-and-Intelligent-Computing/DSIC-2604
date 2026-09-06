-- Sampel MMSI beku untuk Q4 (entity robustness).
-- AIS_POS memuat 25.130 MMSI unik menurut artikel MMDEC.
-- Jalankan SEKALI, simpan hasilnya ke data/manifests/, lalu jangan diulang:
-- literal Q4 harus identik di seluruh layout variant.
SELECT Mmsi, COUNT(*) AS n
FROM iceberg.dsic2604.ais_pos_128
GROUP BY Mmsi
ORDER BY n DESC
LIMIT 50;
