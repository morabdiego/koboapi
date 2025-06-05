"""Optimized HTTP client for KoboAPI requests."""

import requests
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from .exceptions import AuthenticationError, ResourceNotFoundError, KoboAPIError

class Client:
    """
    Optimized HTTP client with better error handling and configuration.
    """

    # Status code mappings
    ERROR_MAPPING = {
        401: AuthenticationError,
        404: ResourceNotFoundError,
    }

    def __init__(
            self, token: str, base_url: str, debug: bool = False,
            timeout: int = 30, max_retries: int = 3
            ):
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.debug = debug
        self.timeout = timeout
        self.max_retries = max_retries

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create configured session with headers."""
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json',
            'User-Agent': 'KoboAPI-Client/1.0'
        })
        return session

    def _build_url(self, endpoint: str) -> str:
        """Build complete URL with proper API versioning."""
        if '/api/v2' not in self.base_url and not endpoint.startswith('/api/v2'):
            endpoint = f'/api/v2{endpoint}' if not endpoint.startswith('/') else f'/api/v2{endpoint}'
        return urljoin(self.base_url, endpoint)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request with improved error handling."""
        return self._make_request('GET', endpoint, params=params)

    def download_file(self, url: str, filepath: str) -> None:
        """Download file with streaming and proper error handling."""
        self._log(f"Downloading: {url} -> {filepath}")

        response = self._make_request_raw('GET', url, stream=True)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        self._log(f"Download completed: {filepath}")

    def _make_request(self, method: str, endpoint: str,
                     params: Optional[Dict] = None,
                     **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retries and error handling."""
        url = self._build_url(endpoint) if not endpoint.startswith('http') else endpoint

        response = self._make_request_raw(method, url, params=params, **kwargs)

        try:
            return response.json()
        except ValueError as e:
            raise KoboAPIError(f"Invalid JSON response: {str(e)}")

    def _make_request_raw(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make raw HTTP request with retries."""
        self._log(f"{method} {url}")

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method, url, timeout=self.timeout, **kwargs
                )
                self._handle_response(response, url)
                return response

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise KoboAPIError(f"Request failed after {self.max_retries} attempts: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff

        raise KoboAPIError("Unexpected error in request handling")

    def _handle_response(self, response: requests.Response, url: str) -> None:
        """Handle HTTP response with appropriate exceptions."""
        if response.ok:
            return

        error_class = self.ERROR_MAPPING.get(response.status_code, KoboAPIError)
        error_msg = f"Request to {url} failed ({response.status_code}): {response.text}"

        raise error_class(error_msg)

    def _log(self, message: str) -> None:
        """Log debug messages if debugging is enabled."""
        if self.debug:
            print(f"[Client] {message}")
