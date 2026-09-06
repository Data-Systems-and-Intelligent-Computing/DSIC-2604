from src.detect_crossover import DifferenceBand, candidate_sign_change, ci_excludes_zero
def test_candidate_crossover():
    a = DifferenceBand(0.01, -10, -15, -5)
    b = DifferenceBand(0.10, 8, 2, 13)
    assert candidate_sign_change(a,b)
    assert ci_excludes_zero(a) and ci_excludes_zero(b)
