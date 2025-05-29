"""HTTP client for KoboAPI requests."""

import requests
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin

class HTTPClient:
    """HTTP client for making requests to Kobo API."""

    def __init__(self, token: str, base_url: str, debug: bool = False, timeout: int = 30):
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.debug = debug
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Token {token}'})

    def _build_url(self, endpoint: str) -> str:
        """Build complete URL ensuring proper API version path."""
        if '/api/v2' not in self.base_url and not endpoint.startswith('/api/v2'):
            endpoint = f'/api/v2{endpoint}' if not endpoint.startswith('/') else f'/api/v2{endpoint}'
        return urljoin(self.base_url, endpoint)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, retries: int = 3) -> Dict[str, Any]:
        """Make GET request with error handling and retries."""
        url = self._build_url(endpoint)

        if self.debug:
            print(f"Making GET request to: {url}")
            if params:
                print(f"Parameters: {params}")

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)

                if response.status_code == 401:
                    raise Exception("Invalid token or unauthorized access")
                elif response.status_code == 404:
                    raise Exception(f"Resource not found: {url}")
                elif not response.ok:
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise Exception(f"Request failed after {retries} attempts: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff

        raise Exception("Unexpected error in request handling")
