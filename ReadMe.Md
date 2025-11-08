MoodTune Music Service

Servicio/API para integración con proveedores de música (Spotify inicialmente). Estructura similar a `moodtune_api` (Flask + Blueprints), con clases OOP para proveedores. Este servicio encapsula la conexión a Spotify para que otros servicios (p. ej. `moodtune_rag`) no usen la API de Spotify directamente.

Características
- Playlists: creación de playlist en Spotify con token del usuario.
- Catálogo: recomendaciones por emoción (Client Credentials) y audio‑features.
- Mapeo centralizado de emoción → rangos valence/energy (`app/src/emotions.py`).

Endpoints principales
- `GET /health` Healthcheck.
- `POST /playlists` Crea una playlist en el proveedor y añade pistas.
- `POST /catalog/audio-features` Audio‑features (valence/energy) por IDs.
- `GET /catalog/emotions` Lista de emociones y parámetros.
- `GET /catalog/emotions/{emotion}` Parámetros para una emoción.

Cuerpo `POST /playlists`
```
{
  "provider": "spotify",
  "provider_access_token": "<token oauth del usuario>",
  "title": "...",
  "description": "...",
  "uris": ["spotify:track:...", "spotify:track:..."]
}
```

Respuesta 201
```
{
  "provider": "spotify",
  "external_playlist_id": "<id>",
  "deep_link_url": "https://open.spotify.com/playlist/<id>",
  "title": "...",
  "description": "...",
  "tracks_added": 20
}
```

OpenAPI y Postman
- OpenAPI: `docs/openapi/moodtune_music.yaml`
- Postman: `docs/openapi/moodtune_music.postman_collection.json`

Requisitos
- Variables en `.env` (usa `.env.example`).
- Para `/playlists`: token OAuth del usuario (este servicio no maneja el login OAuth).
- Para catálogo: `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET` (Client Credentials).

Entorno virtual (venv) local
- Requiere Python 3.11+ instalado.
- Crear y activar entorno (Windows PowerShell):
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
- macOS/Linux (bash/zsh):
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Ejecución local
1. Copia `.env.example` a `.env` y completa valores.
2. `docker compose up --build`
3. API: `http://localhost:8020`.

Ejemplos
```
curl http://localhost:8020/health

curl -X POST http://localhost:8020/catalog/audio-features -H "Content-Type: application/json" -d '{"ids":["6rqhFgbbKwnb9MLmUQDhG6"]}'
```

Novedades
- Nuevos endpoints de resolución de título+artista:
  - `POST /catalog/resolve`
  - `POST /catalog/resolve-batch`
- Proveedor por defecto configurable por `.env` con `DEFAULT_PROVIDER` (`itunes` | `spotify`) para resolución y playlists.

