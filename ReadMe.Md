MoodTune Music Service

Servicio/API de integración con proveedores de música (Spotify e iTunes). Expone operaciones de catálogo y creación de playlists para que otros servicios (por ejemplo `moodtune_rag`) no dependan directamente de APIs externas. Basado en Flask + Blueprints.

Características
- Playlists: creación en el proveedor y agregado de pistas (Spotify soportado).
- Catálogo: recomendaciones por emoción y audio-features (valence/energy) vía Spotify.
- Resolución por título+artista: endpoints para normalizar resultados (iTunes/Spotify).
- Proveedor por defecto configurable vía `.env` (`DEFAULT_PROVIDER=spotify | itunes`).

Endpoints
- `GET /health` Estado del servicio.
- `POST /playlists` Crea una playlist en el proveedor y añade pistas.
- `POST /catalog/audio-features` Obtiene valence/energy por IDs (Spotify).
- `GET /catalog/emotions` Lista emociones y parámetros por defecto.
- `GET /catalog/emotions/{emotion}` Parámetros de una emoción.
- `POST /catalog/resolve` Resuelve título+artista a un track normalizado.
- `POST /catalog/resolve-batch` Resolución en lote.

Ejemplo `POST /playlists`
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
- OpenAPI: `moodtune_music/docs/openapi/moodtune_music.yaml`
- Postman: `moodtune_music/docs/openapi/moodtune_music.postman_collection.json`

Requisitos
- Copia `.env.example` a `.env` y completa valores.
- Para `/playlists`: token OAuth del usuario (este servicio no maneja el login OAuth).
- Para catálogo: `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET` (Client Credentials).

Ejecutar en local (venv)
```
python -m venv .venv
# Linux/Mac: source .venv/bin/activate
# Windows:   .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Docker
```
docker compose up --build
# API en http://localhost:8020
```

Ejemplos
```
curl http://localhost:8020/health
curl -X POST http://localhost:8020/catalog/audio-features -H "Content-Type: application/json" -d '{"ids":["6rqhFgbbKwnb9MLmUQDhG6"]}'
```

Notas
- No expongas credenciales reales en el repositorio; usa `.env.example`.
- `DEFAULT_PROVIDER` también afecta a la resolución de título+artista y puede usarse por `moodtune_rag`.

