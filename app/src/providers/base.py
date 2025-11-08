from typing import List, Dict, Any


class ProviderClient:
    name = "base"

    def create_playlist(self, access_token: str, title: str, description: str) -> Dict[str, Any]:
        raise NotImplementedError

    def add_tracks(self, access_token: str, playlist_id: str, uris: List[str]) -> None:
        raise NotImplementedError

    def make_deeplink(self, playlist_id: str) -> str:
        raise NotImplementedError

