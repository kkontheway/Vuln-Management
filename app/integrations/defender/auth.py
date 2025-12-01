"""Authentication module for Microsoft Defender API."""
import json
import urllib.request
import urllib.parse
import logging
from app.integrations.defender.config import TENANT_ID, APP_ID, APP_SECRET
from app.constants.api import API_BASE_URL_DEFAULT, OAUTH_TOKEN_ENDPOINT

logger = logging.getLogger(__name__)


def get_access_token():
    """Get Microsoft Defender API access token.
    
    Returns:
        str: Access token if successful, None otherwise
    """
    try:
        import ssl
        context = ssl._create_unverified_context()
        
        url = OAUTH_TOKEN_ENDPOINT.format(tenant_id=TENANT_ID)
        resource_app_id_uri = API_BASE_URL_DEFAULT
        
        body = {
            'resource': resource_app_id_uri,
            'client_id': APP_ID,
            'client_secret': APP_SECRET,
            'grant_type': 'client_credentials'
        }
        
        data = urllib.parse.urlencode(body).encode("utf-8")
        req = urllib.request.Request(url, data)
        response = urllib.request.urlopen(req, context=context)
        json_response = json.loads(response.read())
        
        access_token = json_response["access_token"]
        logger.info("Successfully obtained access token")
        
        return access_token
    
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        return None

