import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyAuth:
    def __init__(self, client_id, client_secret, redirect_uri, scope):
        self._mgr = SpotifyOAuth(client_id, client_secret, redirect_uri, scope)

    def exchange_code(self, code):
        token_info = self._mgr.get_access_token(code)
        sp = spotipy.Spotify(auth_manager=self._mgr)
        return token_info, sp

    def from_refresh_token(self, refresh_token):
        token_info = self._mgr.refresh_access_token(refresh_token)
        sp = spotipy.Spotify(auth_manager=self._mgr)
        return token_info, sp
