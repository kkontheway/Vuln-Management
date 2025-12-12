"""Register all FastAPI routers."""
from fastapi import FastAPI

from app.routes import (
    vulnerabilities,
    snapshots,
    dashboard_trends,
    sync,
    servicenow,
    threat_intelligence,
    chat,
    recommendations,
    integrations,
)


def register_routers(app: FastAPI):
    """Register all API routers with the FastAPI app."""
    routers = [
        vulnerabilities.router,
        snapshots.router,
        dashboard_trends.router,
        sync.router,
        servicenow.router,
        threat_intelligence.router,
        chat.router,
        recommendations.router,
        integrations.router,
    ]
    for router in routers:
        app.include_router(router)
