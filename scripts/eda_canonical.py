import json
from pathlib import Path
import pyarrow.parquet as pq
import duckdb

parquet_path = Path("D:/DSIC-2604/Dataset/Dataset_AIS_POS.parquet")
pf = pq.ParquetFile(parquet_path)
meta = pf.metadata

total_uncompressed = sum(
    meta.row_group(i).column(j).total_uncompressed_size
    for i in range(meta.num_row_groups)
    for j in range(meta.num_columns)
)
total_compressed = sum(
    meta.row_group(i).column(j).total_compressed_size
    for i in range(meta.num_row_groups)
    for j in range(meta.num_columns)
)

con = duckdb.connect()
path_str = str(parquet_path).replace("\\", "/")

query_stats = f"""
    SELECT 
        MIN(c) AS min_rows_per_day,
        MAX(c) AS max_rows_per_day,
        ROUND(AVG(c), 2) AS avg_rows_per_day,
        ROUND(MEDIAN(c), 2) AS median_rows_per_day,
        COUNT(*) AS total_days
    FROM (
        SELECT CAST(Date AS DATE) as d, COUNT(*) as c
        FROM read_parquet('{path_str}')
        GROUP BY d
    )
"""
stats = con.execute(query_stats).fetchone()

query_bounds = f"""
    SELECT 
        MIN(Date) AS min_date,
        MAX(Date) AS max_date
    FROM read_parquet('{path_str}')
"""
bounds = con.execute(query_bounds).fetchone()

result = {
    "file_size_bytes": parquet_path.stat().st_size,
    "file_size_mib": round(parquet_path.stat().st_size / (1024 * 1024), 2),
    "uncompressed_data_bytes": total_uncompressed,
    "uncompressed_data_mib": round(total_uncompressed / (1024 * 1024), 2),
    "compressed_data_bytes": total_compressed,
    "compressed_data_mib": round(total_compressed / (1024 * 1024), 2),
    "compression_ratio": round(total_uncompressed / total_compressed, 3),
    "total_rows": meta.num_rows,
    "num_columns": meta.num_columns,
    "num_row_groups": meta.num_row_groups,
    "date_bounds": {
        "min_date": str(bounds[0]),
        "max_date": str(bounds[1])
    },
    "daily_distribution": {
        "min_rows": stats[0],
        "max_rows": stats[1],
        "avg_rows": stats[2],
        "median_rows": stats[3],
        "total_days": stats[4]
    }
}

print(json.dumps(result, indent=2))
