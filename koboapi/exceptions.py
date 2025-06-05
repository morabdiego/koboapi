"""Custom exceptions for KoboAPI."""

class KoboAPIError(Exception):
    """Base exception for KoboAPI errors."""
    pass

class AuthenticationError(KoboAPIError):
    """Raised when authentication fails."""
    pass

class ResourceNotFoundError(KoboAPIError):
    """Raised when a resource is not found."""
    pass

class DownloadError(KoboAPIError):
    """Raised when file download fails."""
    pass
