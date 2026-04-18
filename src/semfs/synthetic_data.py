"""Synthetic dataset metadata for the semfs scaffold."""


def planned_dataset_sizes() -> dict[str, int]:
    """Return the planned corpus sizes from the feature spec."""
    return {"small_files": 30, "large_files": 5000}
