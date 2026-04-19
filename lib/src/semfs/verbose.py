"""Lightweight verbose reporting helpers for semfs operations."""

import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from time import perf_counter

VerboseMessage = str | Callable[[], str]


def emit_verbose(verbose: bool, message: str) -> None:
    """Write one verbose line when enabled by the caller."""
    if not verbose:
        return
    sys.stdout.write(f"[semfs] {message}\n")


def _resolve_message(message: VerboseMessage | None, default: str) -> str:
    if message is None:
        return default
    if isinstance(message, str):
        return message
    return message()


@contextmanager
def timed_verbose(
    verbose: bool,
    before_message: str,
    *,
    after_message: VerboseMessage | None = None,
    failure_message: VerboseMessage | None = None,
) -> Iterator[None]:
    """Emit a before/after verbose pair around one operation."""
    if not verbose:
        yield
        return

    emit_verbose(verbose=True, message=before_message)
    started = perf_counter()
    try:
        yield
    except Exception:
        failed = _resolve_message(failure_message, _resolve_message(after_message, before_message))
        emit_verbose(
            verbose=True,
            message=f"{failed} failed after {format_seconds(perf_counter() - started)}",
        )
        raise
    emit_verbose(
        verbose=True,
        message=(f"{_resolve_message(after_message, before_message)} in {format_seconds(perf_counter() - started)}"),
    )


def format_seconds(seconds: float) -> str:
    """Format elapsed time with millisecond precision."""
    return f"{seconds:.3f}s"
