import importlib
import os
import threading
import time
from spotify_callback_server import SpotifyCallbackServer
from spotify_auth import SpotifyAuth
from manager.telethon_telegram_manager import TelethonTelegramManager
from track import Track
from lru_cache import LRUCache

spotify_auth = SpotifyAuth()
spotify_manager = None
callback_server = SpotifyCallbackServer()
audio_temp_file_path = r"C:\Users\Andrey\Desktop\VSCode-win32-x64-1.66.1\tempFile.mp3"

sess_path = r"C:\Users\Andrey\Desktop\VSCode-win32-x64-1.66.1\existing.session"
telegram_manager = TelethonTelegramManager(sess_path, os.getenv("TELEGRAM_API_ID"), os.getenv("TELEGRAM_API_HASH"))
telegram_manager.start()

active_track = None
cached_tracks = LRUCache(os.getenv("TRACKS_CACHE_SIZE") or 20)
clean_tracks = os.getenv("CLEAN_TRACKS") or True

threading.Thread(target=callback_server.start, daemon=True).start()

def load_backend_from_env():
    backend_path = os.getenv("TRACKS_BACKEND") or "zero_track_backend.ZeroTrackBackend"
    full_backend_path = "backend." + backend_path
    module_path, class_name = full_backend_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    backend_class = getattr(module, class_name)
    return backend_class()

track_backend = load_backend_from_env()

def get_track(track_info):
    name = track_info["item"]["name"]
    artists = ", ".join(a["name"] for a in track_info["item"]["artists"])
    cover_url = track_info["item"]["album"]["images"][0]["url"]
    album = track_info["item"]["album"]["name"]

    return Track(name, artists, cover_url, album)

while (True):
    try:
        code = callback_server.get_code()
        if (callback_server.get_code() != None):
            token_info, sp = spotify_auth.exchange_code(code)
            spotify_manager = sp
            callback_server.set_code(None)
        if (spotify_manager != None):
            track_info = spotify_manager.current_user_playing_track()
            if (track_info and track_info.get("item")):
                track = get_track(track_info)
                if (active_track != track):
                    if (track in cached_tracks):
                        uploaded_file, msg = cached_tracks[track]
                        active_track = track
                        telegram_manager.save_music(msg, True, None)
                        telegram_manager.save_music(msg, False, None)
                    else:
                        track_backend.recreate(audio_temp_file_path, track)

                        uploaded_file = telegram_manager.upload_file(audio_temp_file_path)

                        msg = telegram_manager.send_file("me", uploaded_file)
                        telegram_manager.save_music(msg.media.document, None, None)

                        active_track = track

                        if (cached_tracks.is_full()):
                            old_track, (old_uploaded_file, old_msg) = cached_tracks.pop_lru()
                            telegram_manager.save_music(old_msg, True, None)
                            telegram_manager.delete_message("me", old_msg.id)

                        cached_tracks.put(track, (uploaded_file, msg))

                        os.remove(audio_temp_file_path)
            else:
                if (clean_tracks):
                    active_track = None
                    while (len(cached_tracks) > 0):
                        old_track, (old_uploaded_file, old_msg) = cached_tracks.pop_lru()
                        telegram_manager.save_music(old_msg, True, None)
                        telegram_manager.delete_message("me", old_msg.id)
    except Exception as e:
        print(f"Error occurred: {e}")
    time.sleep(0.5)
