"""Base integration class for all service integrations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BaseIntegration(ABC):
    """Base class for all service integrations."""
    
    def __init__(self, name: str, cache_duration: int = 300):
        self.name = name
        self.cache_duration = cache_duration
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.authenticated = False
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the connection to the service is working."""
        pass
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[key]
        expiry_time = cache_time + timedelta(seconds=self.cache_duration)
        return datetime.now() < expiry_time
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get data from cache if valid."""
        if self._is_cache_valid(key):
            logger.debug(f"Cache hit for {self.name}:{key}")
            return self._cache.get(key)
        return None
    
    def _set_cache(self, key: str, data: Any) -> None:
        """Store data in cache."""
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.now()
        logger.debug(f"Cached data for {self.name}:{key}")
    
    def _clear_cache(self, key: Optional[str] = None) -> None:
        """Clear cache for specific key or all cache."""
        if key:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get integration status."""
        return {
            "name": self.name,
            "authenticated": self.authenticated,
            "cache_entries": len(self._cache),
            "connection_ok": await self.test_connection() if self.authenticated else False
        }

class IntegrationError(Exception):
    """Base exception for integration errors."""
    pass

class AuthenticationError(IntegrationError):
    """Exception raised when authentication fails."""
    pass

class APIError(IntegrationError):
    """Exception raised when API calls fail."""
    pass 