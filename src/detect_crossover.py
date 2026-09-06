"""Pre-registered crossover helpers."""
from dataclasses import dataclass

@dataclass(frozen=True)
class DifferenceBand:
    selectivity: float
    median_difference: float
    ci_low: float
    ci_high: float

def _sign(x):
    return 0 if x == 0 else (1 if x > 0 else -1)

def candidate_sign_change(a, b):
    return _sign(a.median_difference) != 0 and _sign(b.median_difference) != 0 and _sign(a.median_difference) != _sign(b.median_difference)

def ci_excludes_zero(x):
    return x.ci_low > 0 or x.ci_high < 0
