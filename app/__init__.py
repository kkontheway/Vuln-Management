"""FastAPI application factory."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import config
from app.routes import register_routers
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


@asynccontextmanager
async def _lifespan(_: FastAPI):
    """Run startup tasks for FastAPI lifespan."""
    initialize_app_database()
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=config.APP_TITLE,
        version=config.APP_VERSION,
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routers(app)

    static_folder = config.STATIC_FOLDER
    if os.path.isdir(static_folder):
        app.mount(
            "/",
            StaticFiles(directory=static_folder, html=True),
            name="frontend",
        )
    else:
        logger.warning("Static folder %s not found, skipping mount", static_folder)

    logger.info("FastAPI application initialized")

    return app


app = create_app()
