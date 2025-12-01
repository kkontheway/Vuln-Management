"""ServiceNow API Client handling authentication and requests."""
import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ServiceNowClient:
    """ServiceNow REST API Client."""

    def __init__(self, instance_url: str, username: str, password: str):
        """Initialize client with explicit credentials."""
        self.instance_url = (instance_url or "").rstrip('/')
        self.username = username or ""
        self.password = password or ""

        if not self.instance_url:
            raise ValueError("ServiceNow instance URL is required")
        if not self.username or not self.password:
            raise ValueError("ServiceNow username and password are required")

        self.base_url = f"{self.instance_url}/api/now"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make HTTP request to ServiceNow API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/table/incident')
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"ServiceNow API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"ServiceNow API error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"ServiceNow request error: {e}")
            raise Exception(f"Failed to connect to ServiceNow: {str(e)}")
    
    def create_ticket(self, table: str = 'incident', **kwargs) -> Dict:
        """
        Create a ticket in ServiceNow
        
        Args:
            table: ServiceNow table name (default: 'incident')
            **kwargs: Ticket fields (short_description, description, priority, etc.)
            
        Returns:
            Created ticket data
        """
        endpoint = f'/table/{table}'
        data = kwargs
        result = self._make_request('POST', endpoint, json=data)
        return result.get('result', {})
    
    def get_tickets(self, table: str = 'incident', 
                   sysparm_query: Optional[str] = None,
                   sysparm_limit: int = 100,
                   sysparm_offset: int = 0) -> List[Dict]:
        """
        Get tickets from ServiceNow
        
        Args:
            table: ServiceNow table name (default: 'incident')
            sysparm_query: Encoded query string (e.g., 'priority=1^state=2')
            sysparm_limit: Maximum number of records to return
            sysparm_offset: Starting record number
            
        Returns:
            List of tickets
        """
        endpoint = f'/table/{table}'
        params = {
            'sysparm_limit': sysparm_limit,
            'sysparm_offset': sysparm_offset,
            'sysparm_display_value': 'true',
        }
        if sysparm_query:
            params['sysparm_query'] = sysparm_query
        
        result = self._make_request('GET', endpoint, params=params)
        return result.get('result', [])
    
    def get_ticket(self, table: str, sys_id: str) -> Dict:
        """
        Get a specific ticket by sys_id
        
        Args:
            table: ServiceNow table name
            sys_id: Ticket sys_id
            
        Returns:
            Ticket data
        """
        endpoint = f'/table/{table}/{sys_id}'
        params = {'sysparm_display_value': 'true'}
        result = self._make_request('GET', endpoint, params=params)
        return result.get('result', {})
    
    def get_ticket_notes(self, table: str, sys_id: str) -> List[Dict]:
        """
        Get notes for a specific ticket
        
        Args:
            table: ServiceNow table name
            sys_id: Ticket sys_id
            
        Returns:
            List of notes
        """
        # ServiceNow stores notes in the sys_journal_field table
        endpoint = '/table/sys_journal_field'
        params = {
            'sysparm_query': f'element_id={sys_id}^element={table}',
            'sysparm_orderby': 'sys_created_on',
            'sysparm_display_value': 'true',
        }
        result = self._make_request('GET', endpoint, params=params)
        return result.get('result', [])
    
    def add_ticket_note(self, table: str, sys_id: str, note_text: str) -> Dict:
        """
        Add a note to a ticket
        
        Args:
            table: ServiceNow table name
            sys_id: Ticket sys_id
            note_text: Note text content
            
        Returns:
            Created note data
        """
        endpoint = '/table/sys_journal_field'
        data = {
            'element_id': sys_id,
            'element': table,
            'name': table,
            'value': note_text,
        }
        result = self._make_request('POST', endpoint, json=data)
        return result.get('result', {})
    
    def test_connection(self) -> bool:
        """
        Test connection to ServiceNow instance
        
        Returns:
            True if connection is successful
        """
        try:
            # Try to get user info as a connection test
            endpoint = '/table/sys_user'
            params = {'sysparm_limit': 1}
            self._make_request('GET', endpoint, params=params)
            return True
        except Exception as e:
            logger.error(f"ServiceNow connection test failed: {e}")
            return False


def get_servicenow_client() -> Optional[ServiceNowClient]:
    """Backward compatible helper that reads credentials from settings service."""
    try:
        from app.services.integration_settings_service import (
            PROVIDER_SERVICENOW,
            integration_settings_service,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Unable to import integration settings service: %s", exc)
        return None

    runtime = integration_settings_service.get_runtime_credentials(PROVIDER_SERVICENOW)
    if not runtime:
        logger.warning("ServiceNow integration is not configured")
        return None

    metadata = runtime.get('metadata') or {}
    secrets = runtime.get('secrets') or {}

    try:
        return ServiceNowClient(
            instance_url=metadata.get('instance_url', ''),
            username=metadata.get('username', ''),
            password=secrets.get('password', ''),
        )
    except (ValueError, Exception) as exc:  # noqa: BLE001
        logger.error("Failed to initialize ServiceNow client: %s", exc)
        return None
