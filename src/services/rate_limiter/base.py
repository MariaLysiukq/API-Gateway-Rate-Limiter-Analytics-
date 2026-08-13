from abc import ABC, abstractmethod
from typing import Tuple


class BaseRateLimiter(ABC):
    """An abstract base class for algorithms that limit the number of queries."""

    @abstractmethod
    async def is_allowed(
        self, key: str, limit: int, window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """ Checks whether a new request is permitted.
        
        :param key: A unique identifier (e.g. API key or IP)
        :param limit: Maximum number of requests
        :param window_seconds: Time window in seconds
        :return: Tuple (is_allowed: bool, current_request_count: int)
        """
        pass
