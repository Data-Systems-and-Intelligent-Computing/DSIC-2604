"""Controlled layout generation scaffold.

Only target data-file size may change in the main study.
Keep row-group target, row order, partitioning, compression, schema,
row values, writer version, and encoding settings fixed.
"""
PRIMARY_GRID = [32, 64, 128, 256]

def validate_target(target_mib):
    if target_mib not in PRIMARY_GRID and target_mib != 512:
        raise ValueError(f"Unsupported target size: {target_mib}")

def build_variant(*args, **kwargs):
    raise NotImplementedError(
        "Implement with the exact frozen Spark/Iceberg writer configuration after pilot."
    )
