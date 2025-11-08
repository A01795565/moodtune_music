from flask import Blueprint, jsonify
from ..src.config import Config


bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "moodtune_music",
        "debug": Config.DEBUG,
    }), 200

