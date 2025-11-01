import requests
from typing import Any
from . import constants


class OmnisearchClient:
    """Client for interacting with Obsidian Omnisearch plugin's HTTP API.

    The Omnisearch plugin provides advanced full-text search capabilities including:
    - Fuzzy matching for typo-tolerant searches
    - BM25 relevance scoring
    - OCR support for searching text in images
    - PDF indexing and search
    - Recency boosting for recently modified files
    """

    def __init__(
        self,
        host: str = constants.DEFAULT_OMNISEARCH_HOST,
        port: int = constants.DEFAULT_OMNISEARCH_PORT,
        protocol: str = constants.DEFAULT_OMNISEARCH_PROTOCOL,
        timeout: tuple[int, int] = constants.DEFAULT_TIMEOUT,
    ):
        """Initialize Omnisearch client.

        Args:
            host: Omnisearch HTTP server host
            port: Omnisearch HTTP server port (default: 51361)
            protocol: HTTP protocol (default: "http")
            timeout: Request timeout tuple (connect, read) in seconds
        """
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.timeout = timeout

    def get_base_url(self) -> str:
        """Get base URL for Omnisearch API."""
        return f"{self.protocol}://{self.host}:{self.port}"

    def _safe_call(self, f) -> Any:
        """Execute function with error handling.

        Args:
            f: Function to execute

        Returns:
            Function result

        Raises:
            Exception: If request fails with descriptive error message
        """
        try:
            return f()
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            code = error_data.get("errorCode", -1)
            message = error_data.get("message", "<unknown>")
            raise Exception(f"Omnisearch Error {code}: {message}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Omnisearch request failed: {str(e)}")

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search vault using Omnisearch plugin's advanced search.

        Args:
            query: Search query string

        Returns:
            List of search results from Omnisearch with relevance scoring

        Raises:
            Exception: If connection fails or search errors
        """
        # Build Omnisearch URL
        url = f"{self.get_base_url()}/search"

        # URL-encode the query parameter
        params = {"q": query}

        def call_fn():
            # Note: Omnisearch HTTP API typically doesn't require authentication
            response = requests.get(
                url,
                params=params,
                verify=False,  # Omnisearch may use self-signed certs
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
