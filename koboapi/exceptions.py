"""Custom exceptions for KoboAPI."""

class KoboAPIError(Exception):
    """Base exception for KoboAPI errors."""
    pass

class AuthenticationError(KoboAPIError):
    """Raised when authentication fails."""
    pass

class AssetNotFoundError(KoboAPIError):
    """Raised when an asset is not found."""
    pass

class APIRequestError(KoboAPIError):
    """Raised when API request fails."""
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
