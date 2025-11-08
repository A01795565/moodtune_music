"""Autenticación de Spotify (Client Credentials) orientada a objetos.

Uso:
    auth = SpotifyClientCredentials()
    headers = auth.headers()  # contiene Authorization: Bearer <token>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import os
import time
import requests

from ..config import Config


@dataclass
class SpotifyClientCredentials:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    TOKEN_URL: str = "https://accounts.spotify.com/api/token"
    _access_token: Optional[str] = None
    _token_exp: float = 0.0

    def __post_init__(self):
        if not self.client_id:
            self.client_id = Config.SPOTIFY_CLIENT_ID or os.getenv("SPOTIFY_CLIENT_ID")
        if not self.client_secret:
            self.client_secret = Config.SPOTIFY_CLIENT_SECRET or os.getenv("SPOTIFY_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Faltan SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET en entorno para Client Credentials")

    def _ensure_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._token_exp - 30:
            return self._access_token

        resp = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=20,
        )
        if resp.status_code >= 400:
            # Propagar un error claro para configurar credenciales
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(f"No se pudo obtener token de Spotify (Client Credentials). Revise SPOTIFY_CLIENT_ID/SECRET. Detalle: {detail}")

        data = resp.json()
        self._access_token = data.get("access_token")
        if not self._access_token:
            raise RuntimeError("Respuesta de Spotify sin access_token. Revise credenciales.")
        self._token_exp = now + int(data.get("expires_in", 3600))
        return self._access_token

    def headers(self) -> Dict[str, str]:
        token = self._ensure_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

