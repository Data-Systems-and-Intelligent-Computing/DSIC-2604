from src.validate_equivalence import assert_same_scalar_results
def test_equivalence():
    assert_same_scalar_results({"32":100, "64":100, "128":100, "256":100})
