"""Typed toolkit errors."""


class ToolkitError(Exception):
    """Base error safe for presentation by the command-line interface."""


class ManifestValidationError(ToolkitError):
    """A manifest is malformed or violates a safety boundary."""


class UnsafePathError(ToolkitError):
    """A path escapes or cannot be interpreted inside its workspace."""


class AdapterError(ToolkitError):
    """Base adapter failure."""


class AdapterConfigurationError(AdapterError):
    """An adapter is not safely configured."""


class AdapterExecutionError(AdapterError):
    """An adapter failed while executing a run."""


class AdapterTransientError(AdapterError):
    """An adapter reported a retryable condition."""


class AdapterTimeoutError(AdapterError):
    """An adapter exceeded its execution deadline."""


class ReportParseError(ToolkitError):
    """A report does not match a supported synthetic schema."""
