"""Main application entry point for FastAPI."""
import uvicorn

from app import create_app
from config import config

app = create_app()


def run() -> None:
    """Run development server via uvicorn."""
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run()
