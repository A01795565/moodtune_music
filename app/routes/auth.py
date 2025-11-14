from urllib.parse import urlencode

from flask import Blueprint, jsonify, request

from ..src.config import Config


bp = Blueprint("auth", __name__)


@bp.get("/amazon")
def amazon_authorization():
    """Return the Amazon Music authorization URL to start the OAuth flow."""
    client_id = Config.AMAZON_MUSIC_CLIENT_ID
    redirect_uri = request.args.get("redirect_uri") or Config.AMAZON_MUSIC_AUTH_REDIRECT_URI
    scope = (request.args.get("scope") or Config.AMAZON_MUSIC_AUTH_SCOPE or "music::library:read").strip()

    if not client_id:
        return jsonify({"error": "Falta AMAZON_MUSIC_CLIENT_ID"}), 500
    if not redirect_uri:
        return jsonify({"error": "redirect_uri requerido"}), 400

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
    }
    authorize_url = f"https://www.amazon.com/ap/oa?{urlencode(params)}"
    return jsonify({"authorize_url": authorize_url}), 200
