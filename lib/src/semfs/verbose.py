"""Lightweight verbose reporting helpers for semfs operations."""

import sys


def emit_verbose(verbose: bool, message: str) -> None:
    """Write one verbose line when enabled by the caller."""
    if not verbose:
        return
    sys.stdout.write(f"[semfs] {message}\n")


def format_seconds(seconds: float) -> str:
    """Format elapsed time with millisecond precision."""
    return f"{seconds:.3f}s"
