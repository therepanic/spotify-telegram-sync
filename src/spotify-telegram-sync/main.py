import threading
import time
from spotify_callback_server import SpotifyCallbackServer
from spotify_auth import SpotifyAuth

spotify_auth = SpotifyAuth()
spotify_manager = None
callback_server = SpotifyCallbackServer()

threading.Thread(target=callback_server.start, daemon=True).start()

while (True):
    if (callback_server.get_code() != None):
        code = callback_server.get_code()
        token_info, sp = spotify_auth.exchange_code(code)
        spotify_manager = sp
        callback_server.set_code(None)
    if (spotify_manager != None):
        track_info = spotify_manager.current_user_playing_track()
        if track_info and track_info.get("item"):
            name = track_info["item"]["name"]
            artists = ", ".join(a["name"] for a in track_info["item"]["artists"])
            print(f"Now playing: {name} — {artists}")
        else:
            print("Nothing playing")
    #TODO
    time.sleep(0.5)
