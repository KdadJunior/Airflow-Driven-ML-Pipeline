from src.data.ingest import deterministic_sample_indices


def test_deterministic_sample_indices():
    first = deterministic_sample_indices(100, "2025-01-01", 10, 42)
    second = deterministic_sample_indices(100, "2025-01-01", 10, 42)
    assert first == second
    assert len(first) == 10
    assert len(set(first)) == 10


