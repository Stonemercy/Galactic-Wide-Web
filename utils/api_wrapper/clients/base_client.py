from aiohttp import ClientSession, ClientTimeout, ClientSSLError
from asyncio import sleep
from typing import Optional
from abc import ABC
from utils.logger import GWWLogger


class BaseAPIClient(ABC):
    """
    Base class for all API clients.
    Handles common functionality like session management, retries, and error handling.
    """

    def __init__(
        self,
        base_url: str,
        logger: GWWLogger,
        timeout: int = 5,
        headers: Optional[dict] = None,
    ):
        """
        Args:
            base_url: Base URL for the API
            logger: Logger instance
            timeout: Request timeout in seconds
            headers: Default headers to include in all requests
            rate_limit_delay: Delay between requests in seconds (for rate limiting)
        """
        self.base_url = base_url.rstrip("/")
        self.logger = logger
        self.timeout = ClientTimeout(total=timeout)
        self.default_headers = headers or {}
        self._session: Optional[ClientSession] = None

    async def _get_session(self) -> ClientSession:
        """Get or create an aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                headers=self.default_headers, timeout=self.timeout
            )
        return self._session

    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        retries: int = 2,
    ) -> Optional[dict | list]:
        """
        Make a GET request to the API

        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters
            headers: Additional headers for this request
            retries: Number of retry attempts on failure

        Returns:
            JSON response as dict/list, or None on failure
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self._get_session()

        # Merge headers
        request_headers = {**self.default_headers, **(headers or {})}

        for attempt in range(retries):
            try:
                async with session.get(
                    url=url, params=params, headers=request_headers
                ) as response:
                    self.logger.debug(
                        f"[{self.__class__.__name__}] GET {endpoint} - Status: {response.status}"
                    )

                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        self.logger.warning(
                            f"[{self.__class__.__name__}] GET {endpoint} failed - "
                            f"Status: {response.status}, Attempt {attempt + 1}/{retries}"
                        )

            except ClientSSLError as e:
                self.logger.error(f"SSL Error for {endpoint}: {e}")
                raise
            except Exception as e:
                self.logger.error(
                    f"[{self.__class__.__name__}] Error fetching {endpoint}: {type(e)} {e}"
                )

                # Don't retry on last attempt
                if attempt < retries - 1:
                    await sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    return None

        return None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
