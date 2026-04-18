"""Chunking helpers for the semfs scaffold."""


def chunking_description(edges: str) -> str:
    """Describe the configured chunking strategy."""
    if edges == "auto":
        return "markdown-aware for markdown files, fixed otherwise"
    return "fixed overlapping windows"
