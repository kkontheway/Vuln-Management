"""API client for Microsoft Defender API."""
import json
import requests
import logging
from app.integrations.defender.config import API_BASE_URL
from app.constants.api import (
    ENDPOINT_SOFTWARE_VULNERABILITIES_BY_MACHINE,
    ENDPOINT_ADVANCED_QUERIES
)

logger = logging.getLogger(__name__)


def fetch_device_vulnerabilities(access_token: str) -> list:
    """Fetch device vulnerability data from Microsoft Defender API.
    
    Uses /api/machines/SoftwareVulnerabilitiesByMachine API to get all data (full sync).
    
    Args:
        access_token: Microsoft Defender API access token
        
    Returns:
        list: List of vulnerability records
    """
    results = []
    url = f"{API_BASE_URL}{ENDPOINT_SOFTWARE_VULNERABILITIES_BY_MACHINE}?pageSize=50000"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f"Bearer {access_token}"
    }
    
    while url:
        logger.info(f"Requesting: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if 'value' in data:
                results.extend(data['value'])
                logger.info(f"Fetched {len(data['value'])} records")
                
                if '@odata.nextLink' in data:
                    url = data['@odata.nextLink']
                else:
                    url = None
            else:
                logger.warning("No data in API response")
                url = None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            url = None
    
    logger.info(f"Total fetched {len(results)} records")
    return results


def run_advanced_query(query: str, access_token: str) -> dict:
    """Run advanced query against Microsoft Defender API.
    
    Args:
        query: Query string
        access_token: Microsoft Defender API access token
        
    Returns:
        dict: Query results with schema and data, None if failed
    """
    try:
        url = f"{API_BASE_URL}{ENDPOINT_ADVANCED_QUERIES}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"Bearer {access_token}"
        }
        
        data = json.dumps({'Query': query}).encode("utf-8")
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        
        json_response = response.json()
        return {
            'schema': json_response.get('Schema'),
            'results': json_response.get('Results')
        }
    
    except Exception as e:
        logger.error(f"Advanced query execution failed: {e}")
        return None

