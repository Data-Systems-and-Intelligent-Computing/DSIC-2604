from src.benchmark import randomized_block
def test_randomization_reproducible():
    x=[1,2,3,4]
    assert randomized_block(x,42) == randomized_block(x,42)
