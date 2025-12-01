"""Configuration for Microsoft Defender API integration."""
import os
from dotenv import load_dotenv

load_dotenv()

# Microsoft Entra ID / Azure AD authentication configuration
TENANT_ID = os.getenv("TENANT_ID")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
# Can select nearest API endpoint based on geography
REGION_ENDPOINT = os.getenv("REGION_ENDPOINT", "api.securitycenter.microsoft.com")
API_BASE_URL = f"https://{REGION_ENDPOINT}"

# Database configuration
DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'port': int(os.getenv("DB_PORT", 3306)),
    'database': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD")
}

