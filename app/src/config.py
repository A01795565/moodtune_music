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

    # Amazon Music Search / Audio Features (client credentials only)
    AMAZON_MUSIC_API_BASE = os.getenv("AMAZON_MUSIC_API_BASE", "https://api.music.amazon.dev/v1")
    AMAZON_MUSIC_CLIENT_ID = os.getenv("AMAZON_MUSIC_CLIENT_ID")
    AMAZON_MUSIC_CLIENT_SECRET = os.getenv("AMAZON_MUSIC_CLIENT_SECRET")
    AMAZON_MUSIC_TOKEN_SCOPE = os.getenv("AMAZON_MUSIC_TOKEN_SCOPE", "music:catalog")
    AMAZON_MUSIC_TOKEN_URL = os.getenv("AMAZON_MUSIC_TOKEN_URL", "https://api.amazon.com/auth/o2/token")
    AMAZON_MUSIC_COUNTRY = os.getenv("AMAZON_MUSIC_COUNTRY", "US")
    AMAZON_MUSIC_AUTH_SCOPE = os.getenv("AMAZON_MUSIC_AUTH_SCOPE", "music::library:read")
    AMAZON_MUSIC_AUTH_REDIRECT_URI = os.getenv("AMAZON_MUSIC_AUTH_REDIRECT_URI")

    # Spotify OAuth (Authorization Code + PKCE)
    SPOTIFY_AUTH_REDIRECT_URI = os.getenv("SPOTIFY_AUTH_REDIRECT_URI")
    SPOTIFY_AUTH_SCOPES = os.getenv("SPOTIFY_AUTH_SCOPES", "playlist-modify-public playlist-modify-private")

    # Tokens de usuario/servicio para crear playlists en proveedores
    SPOTIFY_USER_TOKEN = os.getenv("SPOTIFY_USER_TOKEN")
    APPLE_MUSIC_USER_TOKEN = os.getenv("APPLE_MUSIC_USER_TOKEN")
    AMAZON_MUSIC_USER_TOKEN = os.getenv("AMAZON_MUSIC_USER_TOKEN")
