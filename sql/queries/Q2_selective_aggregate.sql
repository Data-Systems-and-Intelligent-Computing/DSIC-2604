SELECT AVG(SpeedOverGround) AS avg_sog, MAX(SpeedOverGround) AS max_sog
FROM {{TABLE}}
WHERE Date BETWEEN TIMESTAMP '{{START_TS}}' AND TIMESTAMP '{{END_TS}}';
