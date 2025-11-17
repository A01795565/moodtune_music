"""Autenticación de Spotify (Client Credentials) orientada a objetos.

Uso:
    auth = SpotifyClientCredentials()
    headers = auth.headers()  # contiene Authorization: Bearer <token>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import os
import requests

from ..config import Config
from .client_credentials import ClientCredentials


@dataclass
class SpotifyClientCredentials(ClientCredentials):
    TOKEN_URL: str = "https://accounts.spotify.com/api/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        client_id = client_id or Config.SPOTIFY_CLIENT_ID or os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = client_secret or Config.SPOTIFY_CLIENT_SECRET or os.getenv("SPOTIFY_CLIENT_SECRET")
        super().__init__(client_id=client_id, client_secret=client_secret, token_url=self.TOKEN_URL)

    def _fetch_token(self):
        payload = {"grant_type": "client_credentials", "scope": "playlist-modify-public"}
        resp = requests.post(
            self.token_url,
            data=payload,
            auth=(self.client_id, self.client_secret),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json() or {}
        return data.get("access_token"), int(data.get("expires_in", 3600))

    def headers(self) -> Dict[str, str]:
        token = self.token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
