"""Custom exceptions for semfs."""


class SemfsError(Exception):
    """Base exception for semfs failures."""


class ConfigError(SemfsError):
    """Raised when config or query validation fails."""


class IndexStateError(SemfsError):
    """Raised when persisted index state is missing, unusable, or unreadable."""


class FileProcessingError(SemfsError):
    """Raised when a source file or target directory cannot be processed."""
