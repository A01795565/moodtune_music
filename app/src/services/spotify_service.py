"""Servicio OOP para consumir el catálogo de Spotify (audio-features y búsqueda).

Usa Client Credentials; no requiere tokens de usuario.
"""

from typing import Dict, Any, List
import requests

from ..config import Config
from .spotify_auth import SpotifyClientCredentials
from .base import ServiceProvider


class SpotifyService(ServiceProvider):
    API_BASE = "https://api.spotify.com/v1"
    name = "spotify"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None, market: str | None = None):
        self.market = (market or Config.SPOTIFY_MARKET).upper()
        self.auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)

    def audio_features(self, track_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not track_ids:
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for i in range(0, len(track_ids), 100):
            chunk = track_ids[i:i+100]
            r = requests.get(
                f"{self.API_BASE}/audio-features",
                headers=self.auth.headers(),
                params={"ids": ",".join(chunk)},
                timeout=20,
            )
            if r.status_code >= 500:
                continue
            r.raise_for_status()
            for af in (r.json().get("audio_features") or []):
                if not af:
                    continue
                out[af.get("id")] = af
        return out

    def search_tracks(self, title: str, artist: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Busca pistas por título + artista usando /v1/search (Client Credentials).

        Devuelve una lista de objetos de pista de Spotify (raw) con álbum e imágenes.
        """
        if not title or not artist:
            return []
        q = f"track:{title} artist:{artist}"
        try:
            r = requests.get(
                f"{self.API_BASE}/search",
                headers=self.auth.headers(),
                params={
                    "q": q,
                    "type": "track",
                    "limit": max(1, min(limit, 50)),
                    "market": self.market,
                },
                timeout=20,
            )
            if r.status_code >= 500:
                return []
            r.raise_for_status()
            data = r.json() or {}
            return (data.get("tracks") or {}).get("items") or []
        except Exception:
            return []

