"""Cliente de Amazon Music (servicio no oficial) para búsquedas + audio features."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from time import time

import requests

from ..config import Config
from .base import ServiceProvider
from .client_credentials import ClientCredentials
from .spotify_service import SpotifyService


def _first_value(item: Optional[Dict[str, Any]], *keys: str) -> Any:
    if not item:
        return None
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None


def _extract_artist_name(item: Dict[str, Any]) -> Optional[str]:
    artists = item.get("artists") or item.get("artist") or item.get("primary_artist")
    if isinstance(artists, list):
        for artist in artists:
            if isinstance(artist, dict):
                name = _first_value(
                    artist, "name", "artistName", "artist", "primaryArtist"
                )
                if name:
                    return name
            elif isinstance(artist, str):
                return artist
    if isinstance(artists, dict):
        return _first_value(
            artists, "name", "artistName", "artist", "primaryArtist"
        )
    return _first_value(item, "artist", "artistName", "artist_name", "primaryArtist")



class AmazonClientCredentials(ClientCredentials):
    def _fetch_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            payload["scope"] = self.scope
        resp = requests.post(
            self.token_url,
            data=payload,
            auth=(self.client_id, self.client_secret),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json() or {}
        return data.get("access_token") or data.get("token"), int(data.get("expires_in", 3600))


class AmazonMusicService(ServiceProvider):
    """Facade para el API oficial de Amazon Music (`https://api.music.amazon.dev/v1`)."""

    name = "amazon_music"

    def __init__(
        self,
        api_base: str | None = None,
        country: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.api_base = (api_base or Config.AMAZON_MUSIC_API_BASE or "").rstrip("/")
        if not self.api_base:
            self.api_base = "https://api.music.amazon.dev/v1"
        self.client_id = client_id or Config.AMAZON_MUSIC_CLIENT_ID
        self.client_secret = client_secret or Config.AMAZON_MUSIC_CLIENT_SECRET
        self.scope = Config.AMAZON_MUSIC_TOKEN_SCOPE
        if not (self.client_id and self.client_secret):
            raise RuntimeError(
                "Amazon Music requiere AMAZON_MUSIC_CLIENT_ID y AMAZON_MUSIC_CLIENT_SECRET"
            )
        self._credential_provider = AmazonClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_url=Config.AMAZON_MUSIC_TOKEN_URL,
            scope=self.scope,
        )
        self.country = (country or Config.AMAZON_MUSIC_COUNTRY or "US").upper()
        self._spotify: Optional[SpotifyService] = None

    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._ensure_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, route: str, *, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        try:
            resp = requests.get(
                f"{self.api_base}/{route.lstrip('/')}",
                params=params,
                headers=self._auth_headers(),
                timeout=20,
            )
            if resp.status_code >= 500:
                return {}
            resp.raise_for_status()
            return resp.json() or {}
        except requests.RequestException:
            return {}

    def _ensure_token(self) -> str:
        now = time()
        try:
            return self._credential_provider.token()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"No se pudo obtener token de Amazon Music: {exc}"
            ) from exc

    def search_tracks(self, title: str, artist: str, limit: int = 1) -> List[Dict[str, Any]]:
        if not title or not artist:
            return []
        params = {
            "query": f"{title} {artist}",
            "type": "track",
            "max_results": max(1, min(limit, 50)),
            "country": self.country,
        }
        data = self._request("search", params=params)
        results = data.get("results") or []
        if isinstance(results, dict):
            results = results.get("items") or []
        if not isinstance(results, list):
            return []
        track_results = [
            item
            for item in results
            if str(item.get("type", "track")).lower() in ("track", "song", "music", "")
        ]
        return track_results[: params["max_results"]]

    def _track_metadata(self, track_id: str) -> Dict[str, Any]:
        data = self._request("track", params={"id": track_id, "country": self.country})
        payload = data.get("data") or data
        if isinstance(payload, list):
            payload = payload[0] if payload else {}
        if not isinstance(payload, dict):
            return {}
        return payload

    def _spotify_service(self) -> SpotifyService:
        if self._spotify is None:
            self._spotify = SpotifyService()
        return self._spotify

    def _match_spotify_track(self, title: Optional[str], artist: Optional[str]) -> Optional[str]:
        if not title or not artist:
            return None
        svc = self._spotify_service()
        results = svc.search_tracks(title, artist, limit=1)
        if not results:
            return None
        return results[0].get("id")

    def audio_features(self, track_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not track_ids:
            return {}
        amazon_to_spotify: Dict[str, str] = {}
        for amazon_id in set(track_ids):
            metadata = self._track_metadata(amazon_id)
            title = _first_value(metadata, "title", "name", "trackName")
            artist = _extract_artist_name(metadata)
            if not title or not artist:
                continue
            spotify_id = self._match_spotify_track(title, artist)
            if spotify_id:
                amazon_to_spotify[amazon_id] = spotify_id
        if not amazon_to_spotify:
            return {}
        spotify_features = self._spotify_service().audio_features(list(set(amazon_to_spotify.values())))
        out: Dict[str, Dict[str, Any]] = {}
        for amazon_id, spotify_id in amazon_to_spotify.items():
            if feat := spotify_features.get(spotify_id):
                out[amazon_id] = feat
        return out
