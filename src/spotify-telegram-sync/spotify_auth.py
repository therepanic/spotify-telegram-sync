import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyAuth:
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, scope=None):
        self._mgr = SpotifyOAuth(
            client_id=client_id or os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=client_secret or os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI"),
            scope=scope or os.getenv("SPOTIFY_SCOPE"),
        )

    def exchange_code(self, code):
        token_info = self._mgr.get_access_token(code)
        sp = spotipy.Spotify(auth_manager=self._mgr)
        return token_info, sp
