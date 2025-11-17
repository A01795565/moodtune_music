from typing import List, Dict, Any, Optional
import requests
from ..utils import backoff_retry
from .base import ProviderClient


class SpotifyProvider(ProviderClient):
    name = "spotify"

    API_BASE = "https://api.spotify.com/v1"

    def _auth_headers(self, token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _resolve_user_id(self, access_token: str, provider_user_id: Optional[str]) -> str:
        if provider_user_id:
            return provider_user_id
        r = requests.get(f"{self.API_BASE}/me", headers=self._auth_headers(access_token), timeout=20)
        if r.status_code >= 500:
            raise RuntimeError(f"Spotify error {r.status_code}")
        r.raise_for_status()
        data = r.json() or {}
        user_id = data.get("id")
        if not user_id:
            raise RuntimeError("No se pudo determinar el user_id de Spotify")
        return user_id

    def create_playlist(self, access_token: str, title: str, description: str, provider_user_id: Optional[str] = None) -> Dict[str, Any]:
        def _do():
            user_id = self._resolve_user_id(access_token, provider_user_id)
            r = requests.post(
                f"{self.API_BASE}/users/{user_id}/playlists",
                headers=self._auth_headers(access_token),
                json={"name": title, "description": description, "public": False},
                timeout=20,
            )
            if r.status_code >= 500:
                raise RuntimeError(f"Spotify error {r.status_code}")
            if r.status_code >= 400:
                # no retry on client error
                raise requests.HTTPError(r.text, response=r)
            return r.json()

        return backoff_retry(_do, max_tries=3)

    def add_tracks(self, access_token: str, playlist_id: str, uris: List[str]) -> None:
        def _do():
            r = requests.post(
                f"{self.API_BASE}/playlists/{playlist_id}/tracks",
                headers=self._auth_headers(access_token),
                json={"uris": uris},
                timeout=20,
            )
            if r.status_code >= 500:
                raise RuntimeError(f"Spotify error {r.status_code}")
            if r.status_code >= 400:
                raise requests.HTTPError(r.text, response=r)
            return None

        return backoff_retry(_do, max_tries=3)

    def make_deeplink(self, playlist_id: str) -> str:
        return f"https://open.spotify.com/playlist/{playlist_id}"

    def fetch_playlist(self, access_token: str, playlist_id: str) -> Dict[str, Any]:
        def _fetch(url: str):
            r = requests.get(url, headers=self._auth_headers(access_token), params={"market": "US"}, timeout=20)
            if r.status_code >= 500:
                raise RuntimeError(f"Spotify error {r.status_code}")
            r.raise_for_status()
            return r.json()

        data = _fetch(f"{self.API_BASE}/playlists/{playlist_id}")
        playlist_tracks = []
        tracks_data = data.get("tracks") or {}
        items = tracks_data.get("items") or []
        next_url = tracks_data.get("next")

        def _transform(item: Dict[str, Any]) -> Dict[str, Any]:
            track = item.get("track") or {}
            artists = ", ".join(a.get("name") for a in (track.get("artists") or []) if a.get("name"))
            album = (track.get("album") or {}).get("name")
            images = (track.get("album") or {}).get("images") or []
            image_url = images[0]["url"] if images else None
            return {
                "id": track.get("id"),
                "uri": track.get("uri"),
                "title": track.get("name"),
                "artist": artists,
                "album": album,
                "duration_ms": track.get("duration_ms"),
                "preview_url": track.get("preview_url"),
                "image_url": image_url,
                "external_urls": track.get("external_urls"),
                "added_at": item.get("added_at"),
            }

        playlist_tracks.extend([_transform(it) for it in items if it.get("track")])

        while next_url:
            next_data = _fetch(next_url)
            next_items = (next_data.get("items") or []) if "items" in next_data else []
            playlist_tracks.extend([_transform(it) for it in next_items if it.get("track")])
            next_url = next_data.get("next")

        return {
            "provider": self.name,
            "playlist_id": data.get("id") or playlist_id,
            "title": data.get("name"),
            "description": data.get("description"),
            "owner": (data.get("owner") or {}).get("display_name"),
            "tracks": playlist_tracks,
            "tracks_total": data.get("tracks", {}).get("total", len(playlist_tracks)),
            "images": data.get("images"),
            "external_url": (data.get("external_urls") or {}).get("spotify"),
        }
