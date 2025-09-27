from flask import Flask
from flask_cors import CORS

from . import bp, cli, logger, scheduler, store
from .cache import cache
from .config import Config


def create_app():
    app = Flask(__name__)

    config = Config()
    app.config.from_object(config)

    logger.init_app(app)

    CORS(app, origins=[config.ALLOWED_ORIGINS])

    cache.init_app(app)

    store.init_app(app)

    scheduler.init_app(app)

    cli.init_app(app)

    app.register_blueprint(bp.api_bp)

    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    return app
