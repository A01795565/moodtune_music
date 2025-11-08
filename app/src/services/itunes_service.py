"""Servicio OOP para consumir iTunes Search API (Apple).

Centraliza llamadas para evitar dependencias directas a la API desde rutas.
"""

from typing import Dict, Any, List
import requests

from ..config import Config
from .base import ServiceProvider


class ItunesService(ServiceProvider):
    API_BASE = "https://itunes.apple.com"
    name = "itunes"

    def __init__(self, country: str | None = None):
        self.country = (country or Config.ITUNES_COUNTRY).upper()

    def search_tracks(self, title: str, artist: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Busca canciones por título + artista usando /search.

        Devuelve una lista de resultados crudos del API de iTunes.
        """
        if not title or not artist:
            return []
        try:
            params = {
                "term": f"{title} {artist}",
                "media": "music",
                "entity": "song",
                "limit": max(1, min(limit, 50)),
                "country": self.country,
            }
            r = requests.get(f"{self.API_BASE}/search", params=params, timeout=15)
            if r.status_code >= 500:
                return []
            r.raise_for_status()
            data = r.json() or {}
            return data.get("results") or []
        except Exception:
            return []

