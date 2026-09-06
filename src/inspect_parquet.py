"""Inspect realized file-size and row-group distributions (gate G3 / G4).

Target writer bukan ground truth. Seluruh keputusan grid dan klaim
"file size berbeda" harus bersandar pada distribusi realized di modul ini.
"""
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

MIB = 2**20

# Jumlah file minimum pada kondisi file-size terbesar. Di bawah ini, jumlah
# split terlalu sedikit untuk membedakan efek file-size dari efek paralelisme.
MIN_FILES_LARGEST_CONDITION = 8
PREFERRED_MIN_FILES_LARGEST_CONDITION = 16


def inspect_directory(directory):
    files = sorted(Path(directory).glob("*.parquet"))
    sizes = np.array([p.stat().st_size for p in files], dtype=float)
    rgs, rows, rg_per_file = [], 0, []
    for p in files:
        pf = pq.ParquetFile(p)
        rows += pf.metadata.num_rows
        n = pf.metadata.num_row_groups
        rg_per_file.append(n)
        for i in range(n):
            rgs.append(pf.metadata.row_group(i).total_byte_size)
    rgs = np.asarray(rgs, dtype=float)
    return {
        "directory": str(directory),
        "file_count": len(files),
        "row_count": int(rows),
        "file_size_mib_median": float(np.median(sizes) / MIB) if len(sizes) else None,
        "file_size_mib_p25": float(np.quantile(sizes, 0.25) / MIB) if len(sizes) else None,
        "file_size_mib_p75": float(np.quantile(sizes, 0.75) / MIB) if len(sizes) else None,
        "file_size_mib_iqr": float(
            (np.quantile(sizes, 0.75) - np.quantile(sizes, 0.25)) / MIB
        ) if len(sizes) else None,
        "file_size_mib_min": float(np.min(sizes) / MIB) if len(sizes) else None,
        "file_size_mib_max": float(np.max(sizes) / MIB) if len(sizes) else None,
        "file_size_cv": float(np.std(sizes) / np.mean(sizes))
        if len(sizes) and np.mean(sizes)
        else None,
        "total_size_mib": float(np.sum(sizes) / MIB) if len(sizes) else 0.0,
        "row_group_mib_median": float(np.median(rgs) / MIB) if len(rgs) else None,
        "row_group_mib_min": float(np.min(rgs) / MIB) if len(rgs) else None,
        "row_group_mib_max": float(np.max(rgs) / MIB) if len(rgs) else None,
        "row_group_count": int(len(rgs)),
        "row_groups_per_file_median": float(np.median(rg_per_file)) if rg_per_file else None,
        "file_sizes_bytes": sizes.tolist(),
    }


def file_size_separation(smaller, larger):
    """Apakah dua variant benar-benar terpisah pada sumbu ukuran file?

    `smaller` dan `larger` adalah hasil `inspect_directory`. Gate G3 gagal bila
    rentang interkuartil kedua variant bertumpuk: tanpa pemisahan, "efek file
    size" tidak dapat dibedakan dari variasi penulisan.
    """
    a_lo, a_hi = smaller["file_size_mib_p25"], smaller["file_size_mib_p75"]
    b_lo, b_hi = larger["file_size_mib_p25"], larger["file_size_mib_p75"]
    if None in (a_lo, a_hi, b_lo, b_hi):
        raise ValueError("Distribusi kosong: tidak ada file Parquet untuk diperiksa")

    iqr_overlap = a_hi >= b_lo
    median_ratio = larger["file_size_mib_median"] / smaller["file_size_mib_median"]
    return {
        "smaller_median_mib": smaller["file_size_mib_median"],
        "larger_median_mib": larger["file_size_mib_median"],
        "median_ratio": median_ratio,
        "iqr_overlap": bool(iqr_overlap),
        "range_overlap": bool(smaller["file_size_mib_max"] >= larger["file_size_mib_min"]),
        "separated": bool((not iqr_overlap) and median_ratio >= 1.5),
    }


def row_group_control(variants, tolerance=0.25):
    """Verifikasi target row-group tetap sama antar-variant (gate G4).

    Ini kontrol konstruk utama: jika row-group ikut berskala bersama file size,
    efek keduanya tidak terpisahkan.
    """
    medians = {k: v["row_group_mib_median"] for k, v in variants.items()}
    values = [m for m in medians.values() if m is not None]
    if not values:
        raise ValueError("Tidak ada metadata row-group untuk diperiksa")
    lo, hi = min(values), max(values)
    spread = (hi - lo) / lo if lo else float("inf")
    return {
        "row_group_mib_median_by_variant": medians,
        "relative_spread": spread,
        "controlled": bool(spread <= tolerance),
    }


def grid_is_feasible(largest_variant, minimum=MIN_FILES_LARGEST_CONDITION):
    """Apakah kondisi file-size terbesar menghasilkan cukup file?

    Ukuran tabel kanonik membatasi grid: jumlah file pada kondisi terbesar
    kira-kira ukuran_tabel / target_file_size. Bila hasilnya di bawah `minimum`,
    grid harus diturunkan skalanya (lihat fallback_file_sizes_mib di
    configs/layout.yaml), bukan dipaksakan.
    """
    count = largest_variant["file_count"]
    return {
        "file_count": count,
        "minimum_required": minimum,
        "preferred": PREFERRED_MIN_FILES_LARGEST_CONDITION,
        "feasible": bool(count >= minimum),
        "preferred_met": bool(count >= PREFERRED_MIN_FILES_LARGEST_CONDITION),
    }


def projected_file_count(table_size_mib, target_file_size_mib):
    """Proyeksi jumlah file sebelum layout dibuat, untuk memilih grid di E1."""
    if target_file_size_mib <= 0:
        raise ValueError("target_file_size_mib harus positif")
    return max(1, int(table_size_mib // target_file_size_mib))
