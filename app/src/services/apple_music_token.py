from __future__ import annotations

import os
from typing import Optional, Tuple

from ..config import Config
from .client_credentials import ClientCredentials


class AppleMusicStaticToken(ClientCredentials):
    """Wrapper para usar APPLE_MUSIC_USER_TOKEN con la interfaz ClientCredentials."""

    def __init__(self, user_token: Optional[str] = None, ttl_seconds: int = 3600):
        token = (user_token or Config.APPLE_MUSIC_USER_TOKEN or os.getenv("APPLE_MUSIC_USER_TOKEN") or "").strip()
        if not token:
            raise RuntimeError("APPLE_MUSIC_USER_TOKEN no configurado")
        self._static_token = token
        self._ttl = ttl_seconds
        super().__init__(client_id="apple_music", client_secret="static", token_url="apple_music_static")

    def _fetch_token(self) -> Tuple[Optional[str], int]:
        return self._static_token, self._ttl
