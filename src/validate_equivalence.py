"""Semantic equivalence checks across layout variants."""
def assert_same_scalar_results(results_by_variant):
    values = list(results_by_variant.values())
    if not values:
        raise ValueError("No results supplied")
    first = values[0]
    for k, v in results_by_variant.items():
        if v != first:
            raise AssertionError(f"Semantic mismatch for {k}: {v} != {first}")
