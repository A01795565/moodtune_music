from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ServiceProvider(ABC):
    """Clase base para servicios de catálogo de música.

    Define la interfaz común para búsqueda y (opcionalmente) audio-features.
    """

    name: str = "provider"

    @abstractmethod
    def search_tracks(self, title: str, artist: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Busca pistas por título + artista y devuelve resultados crudos del proveedor."""
        raise NotImplementedError

    def audio_features(self, track_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Opcional: audio-features para una lista de IDs.

        Los proveedores que no soportan audio-features pueden mantener el default
        que levanta NotImplementedError para detectar usos incorrectos.
        """
        raise NotImplementedError("audio_features no implementado para este proveedor")

