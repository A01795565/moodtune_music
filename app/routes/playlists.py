from flask import Blueprint, jsonify, request
from typing import List, Optional

from ..src.config import Config
from ..src.providers.spotify import SpotifyProvider
from ..src.services.spotify_auth import SpotifyClientCredentials
from ..src.services.amazon_music_service import AmazonClientCredentials
from ..src.services.apple_music_token import AppleMusicStaticToken


bp = Blueprint("playlists", __name__)


def _provider_client(name: str):
    name = (name or Config.DEFAULT_PROVIDER).lower()
    if name == "spotify":
        return SpotifyProvider()
    raise ValueError("Proveedor no soportado")

def _resolve_provider_token(provider_name: str, override: Optional[str]) -> str:
    if override:
        return override
    name = (provider_name or Config.DEFAULT_PROVIDER).lower()
    if name == "spotify":
        token = (Config.SPOTIFY_USER_TOKEN or "").strip()
        if token:
            return token
        try:
            auth = SpotifyClientCredentials()
            return auth.token()
        except Exception as exc:
            raise ValueError(f"No fue posible obtener token de Spotify (configura SPOTIFY_USER_TOKEN o client credentials válidos): {exc}") from exc
    if name == "amazon_music":
        token = (Config.AMAZON_MUSIC_USER_TOKEN or "").strip()
        if token:
            return token
        try:
            auth = AmazonClientCredentials(
                client_id=Config.AMAZON_MUSIC_CLIENT_ID,
                client_secret=Config.AMAZON_MUSIC_CLIENT_SECRET,
                token_url=Config.AMAZON_MUSIC_TOKEN_URL,
                scope=Config.AMAZON_MUSIC_TOKEN_SCOPE,
            )
            return auth.token()
        except Exception as exc:
            raise ValueError(f"No fue posible obtener token de Amazon Music (configura AMAZON_MUSIC_USER_TOKEN o client credentials válidos): {exc}") from exc
    if name == "apple_music":
        token = (Config.APPLE_MUSIC_USER_TOKEN or "").strip()
        if token:
            return token
        try:
            return AppleMusicStaticToken().token()
        except Exception as exc:
            raise ValueError(f"APPLE_MUSIC_USER_TOKEN no configurado (o inválido): {exc}") from exc
    raise ValueError(f"Proveedor {provider_name} no soportado para autenticación gestionada")

def _create_playlist_in_provider(provider_name: str, access_token: str, title: str, description: str, uris: List[str], provider_user_id: Optional[str] = None):
    provider = _provider_client(provider_name)
    created = provider.create_playlist(access_token, title, description, provider_user_id=provider_user_id)
    playlist_id = created.get("id") or created.get("uri", "").split(":")[-1]
    if not playlist_id:
        raise ValueError("No se pudo obtener ID de playlist del proveedor")

    for i in range(0, len(uris), 100):
        provider.add_tracks(access_token, playlist_id, uris[i:i+100])

    deeplink = provider.make_deeplink(playlist_id)
    return {
        "provider": provider.name,
        "external_playlist_id": playlist_id,
        "deep_link_url": deeplink,
        "title": title,
        "description": description,
        "tracks_added": len(uris),
    }


@bp.post("")
def create_playlist():
    try:
        p = request.get_json(force=True) or {}
        provider_name = p.get("provider", Config.DEFAULT_PROVIDER)
        provided_token = p.get("provider_access_token")
        title = p.get("title")
        description = p.get("description") or ""
        uris: List[str] = p.get("uris") or []

        if not title:
            return jsonify({"error": "title requerido"}), 400
        if not uris:
            return jsonify({"error": "uris requerido (lista de tracks)"}), 400
        access_token = _resolve_provider_token(provider_name, provided_token)

        payload = _create_playlist_in_provider(provider_name, access_token, title, description, uris, provider_user_id=p.get("provider_user_id"))
        return jsonify(payload), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "No se pudo crear la playlist", "detail": str(e)}), 502


@bp.post("/moodtune")
def create_playlist_for_moodtune():
    """Endpoint especializado para que MoodTune Frontend guarde playlists completas."""
    try:
        p = request.get_json(force=True) or {}
        provider_name = p.get("provider", Config.DEFAULT_PROVIDER)
        title = p.get("title")
        description = p.get("description") or ""
        uris: List[str] = p.get("uris") or []
        user_id = p.get("user_id")
        inference_id = p.get("inference_id")
        intention = p.get("intention")
        emotion = p.get("emotion")

        if not title:
            return jsonify({"error": "title requerido"}), 400
        if not uris:
            return jsonify({"error": "uris requerido (lista de tracks)"}), 400
        access_token = _resolve_provider_token(provider_name, p.get("provider_access_token"))

        payload = _create_playlist_in_provider(provider_name, access_token, title, description, uris, provider_user_id=p.get("provider_user_id"))
        payload.update({
            "user_id": user_id,
            "inference_id": inference_id,
            "intention": intention,
            "emotion": emotion,
        })
        return jsonify(payload), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "No se pudo crear la playlist", "detail": str(e)}), 502


@bp.post("/content")
def fetch_playlist_content():
    """Recupera una playlist del proveedor externo para mostrarla en frontend."""
    try:
        p = request.get_json(force=True) or {}
        provider_name = p.get("provider", Config.DEFAULT_PROVIDER)
        playlist_id = p.get("external_playlist_id")
        if not playlist_id:
            return jsonify({"error": "external_playlist_id requerido"}), 400
        access_token = _resolve_provider_token(provider_name, p.get("provider_access_token"))
        provider = _provider_client(provider_name)
        if not hasattr(provider, "fetch_playlist"):
            return jsonify({"error": f"Proveedor {provider_name} no soporta lectura de playlists"}), 400
        payload = provider.fetch_playlist(access_token, playlist_id)
        return jsonify(payload), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "No se pudo obtener la playlist", "detail": str(e)}), 502
