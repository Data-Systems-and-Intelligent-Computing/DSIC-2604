"""Latency summary and paired comparison."""
import numpy as np

def summarize_latency_ms(values):
    x = np.asarray(values, dtype=float)
    return {
        "n": int(len(x)),
        "p50": float(np.quantile(x, 0.50)),
        "p95": float(np.quantile(x, 0.95)),
        "iqr": float(np.quantile(x, 0.75)-np.quantile(x, 0.25)),
        "mean": float(np.mean(x)),
        "std": float(np.std(x, ddof=1)) if len(x) > 1 else 0.0,
    }

def paired_difference(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("Paired vectors must have identical shape")
    return a - b
