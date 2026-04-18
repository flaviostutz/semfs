"""Public package surface for the semfs scaffold."""

from semfs.indexer import index
from semfs.search import chunks, files

__all__ = ["__version__", "chunks", "files", "index"]

__version__ = "0.0.1"
