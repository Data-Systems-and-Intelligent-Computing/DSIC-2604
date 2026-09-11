"""
Common utilities for DSIC-2604 benchmark suite.
"""

from pathlib import Path
import hashlib
import json
import yaml
from typing import Any, Dict


def get_project_root() -> Path:
    """Mengembalikan path absolute ke root project."""
    return Path(__file__).resolve().parent.parent


def load_yaml(path: Path | str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def sha256_file(path: Path | str, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def calculate_sha256(file_path: Path | str, block_size: int = 65536) -> str:
    """Menghitung hash SHA-256 berkas biner secara streaming."""
    return sha256_file(file_path, chunk_size=block_size)


def write_jsonl(path: Path | str, record: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def format_bytes(size_bytes: int) -> str:
    """Format bytes ke satuan human-readable (MiB, GiB)."""
    mib = size_bytes / (1024 * 1024)
    gib = size_bytes / (1024 * 1024 * 1024)
    if gib >= 1.0:
        return f"{gib:.2f} GiB ({mib:.2f} MiB)"
    return f"{mib:.2f} MiB"
