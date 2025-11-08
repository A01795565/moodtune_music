import os
from dotenv import load_dotenv


class Config:
    load_dotenv()

    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Proveedor por defecto para operaciones (e.g., playlists, resolución)
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "spotify")

    # Spotify Client Credentials (para catálogo)
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_MARKET = os.getenv("SPOTIFY_MARKET", "US")

    # iTunes Search
    ITUNES_COUNTRY = os.getenv("ITUNES_COUNTRY", "US")

