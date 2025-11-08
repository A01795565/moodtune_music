from typing import List, Dict, Any
import requests
from ..utils import backoff_retry
from .base import ProviderClient


class SpotifyProvider(ProviderClient):
    name = "spotify"

    API_BASE = "https://api.spotify.com/v1"

    def _auth_headers(self, token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def create_playlist(self, access_token: str, title: str, description: str) -> Dict[str, Any]:
        def _do():
            r = requests.post(
                f"{self.API_BASE}/me/playlists",
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

