"""Flask application factory."""
import logging
from flask import Flask
from flask_cors import CORS
from config import config
from app.routes import register_blueprints
from database import get_db_connection

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


def initialize_app_database():
    """Initialize and migrate database on app startup."""
    try:
        connection = get_db_connection()
        if connection:
            # Import here to avoid circular dependency
            from app.integrations.defender.database import initialize_database
            from app.repositories.integration_settings_repository import (
                initialize_integration_settings_tables,
            )
            from app.repositories.recordfuture_repository import (
                initialize_recordfuture_table,
            )
            initialize_database(connection)
            initialize_integration_settings_tables(connection)
            initialize_recordfuture_table(connection)
            connection.close()
            logger.info("Database initialized and migrated successfully")
        else:
            logger.warning("Could not connect to database for initialization")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


def create_app():
    """Create and configure Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(
        __name__,
        static_folder=config.STATIC_FOLDER,
        static_url_path=config.STATIC_URL_PATH
    )
    
    # Configure app
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # Enable CORS
    CORS(app)
    
    # Initialize database on startup
    initialize_app_database()
    
    # Register blueprints
    register_blueprints(app)
    
    logger.info("Flask application initialized")
    
    return app
