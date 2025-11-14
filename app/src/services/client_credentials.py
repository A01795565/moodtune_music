"""Base helper for OAuth client credentials token acquisition with caching."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class ClientCredentials(ABC):
    def __init__(self, client_id: str, client_secret: str, token_url: str, scope: Optional[str] = None):
        if not client_id or not client_secret:
            raise RuntimeError("Client credentials require client_id and client_secret")
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.scope = scope
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    def token(self) -> str:
        now = time.time()
        if self._token and now < self._expires_at - 30:
            return self._token
        value, expires_in = self._fetch_token()
        if not value:
            raise RuntimeError("Client credentials response did not return an access token")
        self._token = value
        self._expires_at = now + (expires_in or 3600)
        return self._token

    @abstractmethod
    def _fetch_token(self) -> Tuple[Optional[str], int]:
        """Return a tuple (access_token, expires_in)."""
