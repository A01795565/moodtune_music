"""Endpoints de catálogo (Spotify) que exponen recomendaciones y audio-features.

Estos endpoints encapsulan la lógica de conexión a Spotify para que otros
servicios (p. ej., moodtune_rag) no dependan directamente de la API de Spotify.
"""

from flask import Blueprint, jsonify, request
from typing import List, Dict, Any

from ..src.services.spotify_service import SpotifyService
from ..src.services.itunes_service import ItunesService
from ..src.emotions import EMOTION_PARAMS
from ..src.config import Config


bp = Blueprint("catalog", __name__)


def _emotion_params(emotion: str) -> Dict[str, tuple[float, float]]:
    return EMOTION_PARAMS.get(emotion.lower(), {"valence": (0.4, 0.6), "energy": (0.4, 0.6)})


@bp.post("/audio-features")
def audio_features():
    try:
        p = request.get_json(force=True) or {}
        ids: List[str] = p.get("ids") or []
        if not ids:
            return jsonify({"error": "ids requerido"}), 400
        svc = SpotifyService()
        feats = svc.audio_features(ids)
        # devolver solo campos de interés
        data = {k: {"valence": v.get("valence"), "energy": v.get("energy")} for k, v in feats.items()}
        return jsonify({"items": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def _normalize_itunes_result(it: Dict[str, Any]) -> Dict[str, Any]:
    track_id = it.get("trackId")
    return {
        "id": f"itunes-{track_id}" if track_id else None,
        "external_id": str(track_id) if track_id else None,
        "provider": "itunes",
        "source": "itunes_search",
        "title": it.get("trackName"),
        "artist": it.get("artistName"),
        "uri": it.get("trackViewUrl") or (f"itunes:track:{track_id}" if track_id else None),
        "preview_url": it.get("previewUrl"),
        "artworkUrl100": it.get("artworkUrl100"),
        "image_url": it.get("artworkUrl100"),
        "thumbnail_url": it.get("artworkUrl60") or it.get("artworkUrl100"),
    }

def _normalize_spotify_result(t: Dict[str, Any]) -> Dict[str, Any]:
    track_id = t.get("id")
    images = ((t.get("album") or {}).get("images") or [])
    image_url = images[0].get("url") if images else None
    thumb_url = images[-1].get("url") if images else image_url
    artists = t.get("artists") or []
    first_artist = artists[0].get("name") if artists else None
    return {
        "id": f"spotify-{track_id}" if track_id else None,
        "external_id": track_id,
        "provider": "spotify",
        "source": "spotify_search",
        "title": t.get("name"),
        "artist": first_artist,
        "uri": t.get("uri"),
        "preview_url": t.get("preview_url"),
        "image_url": image_url,
        "thumbnail_url": thumb_url,
    }

@bp.post("/search-itunes")
def search_itunes_route():
    """Búsqueda simple de canciones usando iTunes Search API.

    Body: { title: str, artist: str, limit?: int }
    Respuesta: { items: [ raw_result_itunes... ] }
    """
    try:
        p = request.get_json(force=True) or {}
        title = (p.get("title") or "").strip()
        artist = (p.get("artist") or "").strip()
        limit = int(p.get("limit") or 1)
        if not title or not artist:
            return jsonify({"error": "title y artist requeridos"}), 400
        items = ItunesService().search_tracks(title, artist, limit=max(1, min(limit, 5)))
        return jsonify({"items": items, "returned": len(items)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.post("/search-spotify")
def search_spotify_route():
    """Búsqueda simple de canciones usando Spotify Search API (Client Credentials).

    Body: { title: str, artist: str, limit?: int }
    Respuesta: { items: [ raw_result_spotify... ] }
    """
    try:
        p = request.get_json(force=True) or {}
        title = (p.get("title") or "").strip()
        artist = (p.get("artist") or "").strip()
        limit = int(p.get("limit") or 1)
        if not title or not artist:
            return jsonify({"error": "title y artist requeridos"}), 400
        svc = SpotifyService()
        items = svc.search_tracks(title, artist, limit=max(1, min(limit, 5)))
        return jsonify({"items": items, "returned": len(items)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.get("/emotions")
def list_emotions():
    try:
        return jsonify({"items": EMOTION_PARAMS}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.get("/emotions/<emotion>")
def emotion_params(emotion: str):
    try:
        params = _emotion_params(emotion)
        if not params:
            return jsonify({"error": "emoción no soportada"}), 404
        return jsonify({"emotion": emotion.lower(), "params": params}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/resolve")
def resolve_track_title_artist():
    """Resuelve título+artista a un objeto normalizado de track.

    Body: { title: str, artist: str, limit?: int }
    Respuesta: { items: [ { id, external_id, provider, source, title, artist, uri, preview_url, artworkUrl100, image_url, thumbnail_url } ] }
    """
    try:
        p = request.get_json(force=True) or {}
        title = (p.get("title") or "").strip()
        artist = (p.get("artist") or "").strip()
        limit = int(p.get("limit") or 1)
        if not title or not artist:
            return jsonify({"error": "title y artist requeridos"}), 400
        provider = Config.DEFAULT_PROVIDER
        items: List[Dict[str, Any]] = []
        if provider == "itunes":
            raw = ItunesService().search_tracks(title, artist, limit=max(1, min(limit, 5)))
            items = [_normalize_itunes_result(x) for x in (raw or [])]
        else:
            svc = SpotifyService()
            raw_sp = svc.search_tracks(title, artist, limit=max(1, min(limit, 5)))
            items = [_normalize_spotify_result(x) for x in (raw_sp or [])]
        items = [i for i in items if (i.get("title") and i.get("artist"))]
        return jsonify({"items": items, "returned": len(items)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/resolve-batch")
def resolve_batch():
    """Resuelve en lote una lista de {title, artist} a objetos normalizados.

    Body: { items: [{ title, artist }...], per_item_limit?: int }
    Respuesta: { items: [ { index, title, artist, items: [normalized...] } ], returned: number }
    """
    try:
        p = request.get_json(force=True) or {}
        items_in: List[Dict[str, Any]] = p.get("items") or []
        per_item_limit = int(p.get("per_item_limit") or 1)
        out: List[Dict[str, Any]] = []
        provider = Config.DEFAULT_PROVIDER
        for idx, it in enumerate(items_in):
            title = (it.get("title") or "").strip()
            artist = (it.get("artist") or "").strip()
            if not title or not artist:
                out.append({"index": idx, "title": title, "artist": artist, "items": []})
                continue
            if provider == "itunes":
                raw = ItunesService().search_tracks(title, artist, limit=max(1, min(per_item_limit, 5)))
                norm = [_normalize_itunes_result(x) for x in (raw or [])]
            else:
                svc = SpotifyService()
                raw_sp = svc.search_tracks(title, artist, limit=max(1, min(per_item_limit, 5)))
                norm = [_normalize_spotify_result(x) for x in (raw_sp or [])]
            norm = [i for i in norm if (i.get("title") and i.get("artist"))]
            out.append({"index": idx, "title": title, "artist": artist, "items": norm})
        return jsonify({"items": out, "returned": len(out)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

