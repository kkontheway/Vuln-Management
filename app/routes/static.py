"""Static file serving routes."""
from flask import Blueprint, send_from_directory, jsonify
from config import config

bp = Blueprint('static', __name__)


@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def serve_react_app(path):
    """Serve React application for all non-API routes."""
    if path.startswith('api/'):
        # This shouldn't happen as API routes are defined above, but just in case
        return jsonify({'error': 'Not found'}), 404
    
    # Try to serve static files first
    try:
        return send_from_directory(config.STATIC_FOLDER, path)
    except:
        # If file doesn't exist, serve index.html (for React Router)
        return send_from_directory(config.STATIC_FOLDER, 'index.html')

