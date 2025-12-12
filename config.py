"""Configuration module for the application."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # Database configuration
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # FastAPI metadata / runtime toggles
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"
    APP_TITLE = os.getenv("APP_TITLE", "Vulnerability Management API")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    
    # Static files
    STATIC_FOLDER = os.getenv("STATIC_FOLDER", "frontend/dist")
    STATIC_URL_PATH = os.getenv("STATIC_URL_PATH", "")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Redis configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    # Integration secrets configuration
    INTEGRATIONS_SECRET_KEY = os.getenv("INTEGRATIONS_SECRET_KEY")
    KEY_VAULT_URL = os.getenv("KEY_VAULT_URL")

    # Threat source enrichment files
    METASPLOIT_CVE_PATH = os.getenv("METASPLOIT_CVE_PATH", "data/metasploit.txt")
    NUCLEI_CVE_PATH = os.getenv("NUCLEI_CVE_PATH", "data/nuclei.txt")

    # Identity provider (Microsoft Entra ID placeholders)
    ENTRA_TENANT_ID = os.getenv("ENTRA_TENANT_ID")
    ENTRA_CLIENT_ID = os.getenv("ENTRA_CLIENT_ID")
    ENTRA_CLIENT_SECRET = os.getenv("ENTRA_CLIENT_SECRET")
    ENTRA_AUTHORITY = os.getenv("ENTRA_AUTHORITY")
    ENTRA_API_SCOPE = os.getenv("ENTRA_API_SCOPE")
    AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "none")

    @property
    def db_config(self):
        """Get database configuration dictionary."""
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
        }

    @property
    def allowed_origins(self):
        """Return configured CORS origins list."""
        raw = os.getenv("ALLOWED_ORIGINS", "*")
        if raw.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


# Global config instance
config = Config()
