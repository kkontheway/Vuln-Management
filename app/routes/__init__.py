"""Register all blueprints."""
from flask import Flask
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
    static
)


def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app.
    
    Args:
        app: Flask application instance
    
    Note: static.bp must be registered last to serve React app for all non-API routes.
    """
    # API routes
    app.register_blueprint(vulnerabilities.bp)
    app.register_blueprint(snapshots.bp)
    app.register_blueprint(dashboard_trends.bp)
    app.register_blueprint(sync.bp)
    app.register_blueprint(servicenow.bp)
    app.register_blueprint(threat_intelligence.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(recommendations.bp)
    app.register_blueprint(integrations.bp)
    
    # Static file serving (must be last)
    app.register_blueprint(static.bp)
