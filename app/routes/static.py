"""Static file serving routes."""
from flask import Blueprint, current_app, jsonify
from werkzeug.exceptions import NotFound

bp = Blueprint('static', __name__)


@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def serve_react_app(path):
    """Serve React application for all non-API routes."""
    path = (path or '').lstrip('/')
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404

    if path:
        try:
            return current_app.send_static_file(path)
        except NotFound:
            pass

    return current_app.send_static_file('index.html')
