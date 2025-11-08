from flask import Blueprint, jsonify, request
from typing import List

from ..src.config import Config
from ..src.providers.spotify import SpotifyProvider


bp = Blueprint("playlists", __name__)


def _provider_client(name: str):
    name = (name or Config.DEFAULT_PROVIDER).lower()
    if name == "spotify":
        return SpotifyProvider()
    raise ValueError("Proveedor no soportado")


@bp.post("")
def create_playlist():
    try:
        p = request.get_json(force=True) or {}
        provider_name = p.get("provider", Config.DEFAULT_PROVIDER)
        access_token = p.get("provider_access_token")
        title = p.get("title")
        description = p.get("description") or ""
        uris: List[str] = p.get("uris") or []

        if not access_token:
            return jsonify({"error": "provider_access_token requerido"}), 400
        if not title:
            return jsonify({"error": "title requerido"}), 400
        if not uris:
            return jsonify({"error": "uris requerido (lista de tracks)"}), 400

        provider = _provider_client(provider_name)
        created = provider.create_playlist(access_token, title, description)
        playlist_id = created.get("id") or created.get("uri", "").split(":")[-1]
        if not playlist_id:
            return jsonify({"error": "No se pudo obtener ID de playlist del proveedor"}), 502

        for i in range(0, len(uris), 100):
            provider.add_tracks(access_token, playlist_id, uris[i:i+100])

        deeplink = provider.make_deeplink(playlist_id)
        return jsonify({
            "provider": provider.name,
            "external_playlist_id": playlist_id,
            "deep_link_url": deeplink,
            "title": title,
            "description": description,
            "tracks_added": len(uris),
        }), 201
    except Exception as e:
        return jsonify({"error": "No se pudo crear la playlist", "detail": str(e)}), 502

