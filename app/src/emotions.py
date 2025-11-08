"""Mapa centralizado de emociones -> rangos valence/energy.

Estos parámetros se usan para orientar recomendaciones/filtrado.
"""

from typing import Dict, Tuple


EMOTION_PARAMS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "happy": {"valence": (0.6, 1.0), "energy": (0.5, 1.0)},
    "sad": {"valence": (0.0, 0.4), "energy": (0.0, 0.5)},
    "angry": {"valence": (0.2, 0.6), "energy": (0.6, 1.0)},
    "relaxed": {"valence": (0.5, 1.0), "energy": (0.0, 0.5)},
}

