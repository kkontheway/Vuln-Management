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
    
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    # Static files
    STATIC_FOLDER = "frontend/dist"
    STATIC_URL_PATH = ""
    
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


# Global config instance
config = Config()
