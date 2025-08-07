# extensions.py

from flask_wtf import CSRFProtect
from flask import request, jsonify
from flask_wtf.csrf import CSRFError

csrf = CSRFProtect()

def init_extensions(app):
    csrf.init_app(app)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request.content_type == "application/json":
            return jsonify({"error": f"CSRF Error: {e.description}"}), 400
        return f"CSRF Error: {e.description}", 400
