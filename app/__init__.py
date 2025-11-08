from flask import Flask, jsonify, request, g
import time
import logging
try:
    from flask_cors import CORS
except Exception:
    CORS = None

from .src.config import Config
from .routes.health import bp as health_bp
from .routes.playlists import bp as playlists_bp
from .routes.catalog import bp as catalog_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if CORS:
        origins = Config.CORS_ORIGINS if hasattr(Config, 'CORS_ORIGINS') else '*'
        CORS(app, resources={r"/*": {"origins": origins}}, supports_credentials=True)

    app.register_blueprint(health_bp)
    app.register_blueprint(playlists_bp, url_prefix="/playlists")
    app.register_blueprint(catalog_bp, url_prefix="/catalog")

    # Logging simple de todas las peticiones entrantes
    logging.basicConfig(level=logging.DEBUG if getattr(Config, 'DEBUG', True) else logging.INFO)

    @app.before_request
    def _log_start():
        g._start_time = time.time()

    @app.after_request
    def _log_request(resp):
        try:
            started = getattr(g, '_start_time', None)
            dur_ms = int((time.time() - started) * 1000) if started else -1
            logging.info(
                "%s %s -> %s (%d ms) ip=%s",
                request.method,
                request.path,
                resp.status_code,
                dur_ms,
                request.headers.get('X-Forwarded-For', request.remote_addr),
            )
        except Exception:
            pass
        return resp

    @app.get("/")
    def root():
        return jsonify({"name": "moodtune_music", "status": "ok"}), 200

    return app
