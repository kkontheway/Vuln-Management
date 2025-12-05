"""Service layer for Microsoft Defender API operations.

This layer encapsulates API call logic, error handling, and retry mechanisms.
It provides a higher-level interface than the API client.
"""
import logging
from typing import Optional, List, Dict, Any
from app.integrations.defender.auth import get_access_token
from app.integrations.defender.api_client import (
    fetch_device_vulnerabilities,
    run_advanced_query
)

logger = logging.getLogger(__name__)


class DefenderService:
    """Service for Microsoft Defender API operations."""
    
    def __init__(self):
        """Initialize the service."""
        self._access_token: Optional[str] = None
    
    def get_access_token(self) -> Optional[str]:
        """Get access token, with caching.
        
        Returns:
            str: Access token if successful, None otherwise
        """
        if not self._access_token:
            self._access_token = get_access_token()
            if not self._access_token:
                logger.error("Failed to obtain access token")
        return self._access_token
    
    def refresh_access_token(self) -> Optional[str]:
        """Force refresh access token.
        
        Returns:
            str: Access token if successful, None otherwise
        """
        self._access_token = get_access_token()
        if not self._access_token:
            logger.error("Failed to refresh access token")
        return self._access_token
    
    def fetch_device_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Fetch device vulnerability data from Microsoft Defender API.
        
        Returns:
            list: List of vulnerability records, empty list on error
        """
        access_token = self.get_access_token()
        if not access_token:
            logger.error("Cannot fetch vulnerabilities: no access token")
            return []
        try:
            vulnerabilities = fetch_device_vulnerabilities(access_token)
            logger.info(f"Successfully fetched {len(vulnerabilities)} vulnerability records")
            return vulnerabilities
        except Exception as e:
            logger.error(f"Error fetching device vulnerabilities: {e}")
            # Try refreshing token once
            access_token = self.refresh_access_token()
            if access_token:
                try:
                    vulnerabilities = fetch_device_vulnerabilities(access_token)
                    logger.info(f"Successfully fetched {len(vulnerabilities)} vulnerability records after token refresh")
                    return vulnerabilities
                except Exception as retry_error:
                    logger.error(f"Error fetching device vulnerabilities after token refresh: {retry_error}")
            return []

    def run_advanced_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Run advanced query against Microsoft Defender API.
        
        Args:
            query: Query string
            
        Returns:
            dict: Query results with schema and data, None if failed
        """
        access_token = self.get_access_token()
        if not access_token:
            logger.error("Cannot run advanced query: no access token")
            return None
        
        try:
            result = run_advanced_query(query, access_token)
            if result:
                logger.info("Successfully executed advanced query")
            return result
        except Exception as e:
            logger.error(f"Error running advanced query: {e}")
            # Try refreshing token once
            access_token = self.refresh_access_token()
            if access_token:
                try:
                    result = run_advanced_query(query, access_token)
                    if result:
                        logger.info("Successfully executed advanced query after token refresh")
                    return result
                except Exception as retry_error:
                    logger.error(f"Error running advanced query after token refresh: {retry_error}")
            return None


# Global service instance
_service_instance: Optional[DefenderService] = None


def get_defender_service() -> DefenderService:
    """Get global Defender service instance.
    
    Returns:
        DefenderService: Service instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = DefenderService()
    return _service_instance
