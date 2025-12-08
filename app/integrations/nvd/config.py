"""Configuration for NVD API integration."""
import os
from dotenv import load_dotenv

load_dotenv()

NVD_API_BASE_URL = os.getenv(
    "NVD_API_BASE_URL",
    "https://services.nvd.nist.gov/rest/json/cves/2.0",
)
NVD_API_KEY = os.getenv("NVD_API_KEY")
NVD_API_TIMEOUT = int(os.getenv("NVD_API_TIMEOUT", 30))
