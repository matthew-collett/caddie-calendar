from flask import Flask
from flask_cors import CORS
from .cache import cache
from .config import Config
from . import store, scheduler, bp, cli, logger


def create_app():
    app = Flask(__name__)
    config = Config()
    app.config.from_object(config)
    logger.init_app(app)
    CORS(app, origins=config.ALLOWED_ORIGINS)
    cache.init_app(app)
    store.init_app(app)
    scheduler.init_app(app)
    cli.init_app(app)
    app.sessions = {}
    app.register_blueprint(bp.api_bp)

    return app
