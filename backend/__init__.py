"""Application factory"""

import os

from flask import Flask

from .config import Config
from .extensions import csrf, db, login_manager, migrate


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="../frontend/template",
        static_folder="../frontend/static",
        instance_path=os.path.join(os.path.dirname(__file__), "instance"),
    )
    app.config.from_object(Config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(
        app,
        db,
        directory=os.path.join(app.root_path, "migrations"),
    )
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    csrf.init_app(app)

    from . import models  # noqa: F401
    from .routes import register_routes

    register_routes(app)
    return app
