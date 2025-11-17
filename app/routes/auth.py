from urllib.parse import urlencode
import os
import secrets
import hashlib
import base64
import time
from typing import Dict, Tuple, Optional

import requests
from flask import Blueprint, jsonify, request

from ..src.config import Config


bp = Blueprint("auth", __name__)

PKCE_STORE: Dict[str, Tuple[str, float, Optional[str]]] = {}  # state -> (verifier, expires_at, callback_url)
PKCE_TTL_SECONDS = 600  # 10 minutos


def _generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)[:128]


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")


def _remember_state(state: str, verifier: str, callback_url: Optional[str] = None) -> None:
    now = time.time()
    # Limpieza simple
    expired = [k for k, (_, exp, _) in PKCE_STORE.items() if exp < now]
    for key in expired:
        PKCE_STORE.pop(key, None)
    PKCE_STORE[state] = (verifier, now + PKCE_TTL_SECONDS, callback_url)


def _pop_state_data(state: str) -> Optional[Tuple[str, Optional[str]]]:
    item = PKCE_STORE.pop(state, None)
    if not item:
        return None
    verifier, expires_at, callback_url = item
    if time.time() > expires_at:
        return None
    return (verifier, callback_url)


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


@bp.get("/spotify")
def spotify_authorization():
    """Devuelve la URL de autorización de Spotify usando PKCE."""
    client_id = Config.SPOTIFY_CLIENT_ID
    redirect_uri = request.args.get("redirect_uri") or os.getenv("SPOTIFY_AUTH_REDIRECT_URI") or getattr(Config, "SPOTIFY_AUTH_REDIRECT_URI", None)
    scopes = (request.args.get("scope") or getattr(Config, "SPOTIFY_AUTH_SCOPES", "playlist-modify-public playlist-modify-private")).strip()

    # Optional callback URL for frontend redirection after OAuth
    callback_url = request.args.get("callback_url")

    print("=" * 80)
    print("GET /auth/spotify - OAuth Init:")
    print(f"  callback_url: {callback_url}")
    print(f"  redirect_uri: {redirect_uri}")
    print("=" * 80)

    if not client_id:
        return jsonify({"error": "Falta SPOTIFY_CLIENT_ID"}), 500
    if not redirect_uri:
        return jsonify({"error": "redirect_uri requerido"}), 400

    code_verifier = _generate_code_verifier()
    code_challenge = _code_challenge(code_verifier)
    state = secrets.token_urlsafe(16)
    _remember_state(state, code_verifier, callback_url)

    print(f"Generated state: {state} (length: {len(state)})")
    print(f"Stored in PKCE_STORE with callback_url: {callback_url}")
    print("=" * 80)

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    authorize_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return jsonify({"authorize_url": authorize_url, "state": state}), 200


@bp.get("/spotify/callback")
def spotify_callback():
    """Intercambia el código de Spotify por tokens usando PKCE y redirige al frontend."""
    from flask import redirect as flask_redirect

    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    print("=" * 80)
    print("GET /auth/spotify/callback - OAuth Callback:")
    print(f"  Received state: {state} (length: {len(state) if state else 0})")
    print(f"  Received code: {code[:20] if code else None}...")
    print(f"  Received error: {error}")
    print(f"  PKCE_STORE keys: {list(PKCE_STORE.keys())}")
    print("=" * 80)

    # Default frontend callback URL
    default_callback = os.getenv("FRONTEND_CALLBACK_URL", "http://localhost:5173/create-playlist")

    # Get state data (verifier and custom callback URL)
    state_data = _pop_state_data(state) if state else None
    verifier = state_data[0] if state_data else None
    frontend_callback = state_data[1] if state_data and state_data[1] else default_callback

    print(f"State lookup result:")
    print(f"  Found in PKCE_STORE: {state_data is not None}")
    print(f"  Verifier exists: {verifier is not None}")
    print(f"  Frontend callback: {frontend_callback}")
    print("=" * 80)

    if error:
        # User denied authorization or other error
        return flask_redirect(f"{frontend_callback}?error={error}")

    if not code or not state:
        return flask_redirect(f"{frontend_callback}?error=missing_code_or_state")

    if not verifier:
        return flask_redirect(f"{frontend_callback}?error=invalid_state")

    redirect_uri = os.getenv("SPOTIFY_AUTH_REDIRECT_URI") or getattr(Config, "SPOTIFY_AUTH_REDIRECT_URI", None)
    if not redirect_uri:
        return flask_redirect(f"{frontend_callback}?error=redirect_uri_not_configured")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": Config.SPOTIFY_CLIENT_ID,
        "code_verifier": verifier,
    }
    auth = None
    if Config.SPOTIFY_CLIENT_SECRET:
        auth = (Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET)
    try:
        resp = requests.post("https://accounts.spotify.com/api/token", data=data, auth=auth, timeout=20)
        if resp.status_code >= 500:
            return flask_redirect(f"{frontend_callback}?error=spotify_server_error")
        resp.raise_for_status()
        payload = resp.json() or {}
    except requests.RequestException:
        return flask_redirect(f"{frontend_callback}?error=token_exchange_failed")

    # Redirect to frontend with tokens in URL hash (more secure than query params)
    access_token = payload.get("access_token", "")
    refresh_token = payload.get("refresh_token", "")
    expires_in = payload.get("expires_in", 3600)
    token_type = payload.get("token_type", "Bearer")
    scope = payload.get("scope", "")

    # Use URL hash to prevent tokens from being logged in server access logs
    redirect_url = f"{frontend_callback}#access_token={access_token}&refresh_token={refresh_token}&expires_in={expires_in}&token_type={token_type}&scope={scope}&state={state}"

    print("=" * 80)
    print("OAuth Callback - Redirecting to frontend:")
    print(f"  Frontend callback: {frontend_callback}")
    print(f"  State being returned: {state} (length: {len(state)})")
    print(f"  Full redirect URL (tokens truncated): {frontend_callback}#...&state={state}")
    print("=" * 80)

    return flask_redirect(redirect_url)


@bp.post("/spotify/refresh")
def spotify_refresh():
    """Refresh Spotify access token using refresh token."""
    body = request.get_json(force=True) or {}
    refresh_token = body.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "refresh_token requerido"}), 400

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": Config.SPOTIFY_CLIENT_ID,
    }

    auth = None
    if Config.SPOTIFY_CLIENT_SECRET:
        auth = (Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET)

    try:
        resp = requests.post("https://accounts.spotify.com/api/token", data=data, auth=auth, timeout=20)
        if resp.status_code >= 500:
            return jsonify({"error": "Spotify token endpoint error", "detail": resp.text}), 502
        resp.raise_for_status()
        payload = resp.json() or {}
    except requests.RequestException as exc:
        return jsonify({"error": "No se pudo refrescar el token", "detail": str(exc)}), 502

    return jsonify({
        "provider": "spotify",
        "token_type": payload.get("token_type"),
        "scope": payload.get("scope"),
        "access_token": payload.get("access_token"),
        "refresh_token": payload.get("refresh_token"),  # Spotify may issue a new one
        "expires_in": payload.get("expires_in"),
    }), 200
