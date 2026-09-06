SELECT MessageType, COUNT(*) AS n, AVG(SpeedOverGround) AS avg_sog
FROM {{TABLE}}
WHERE Date BETWEEN TIMESTAMP '{{START_TS}}' AND TIMESTAMP '{{END_TS}}'
GROUP BY MessageType
ORDER BY MessageType;
