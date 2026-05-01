import importlib
import os
import threading
import time
import asyncio
import convert_tdata_to_session
from spotify_callback_server import SpotifyCallbackServer
from spotify_auth import SpotifyAuth
from manager.telethon_telegram_manager import TelethonTelegramManager
from track import Track
from backend.zero_track_backend import ZeroTrackBackend
from track_sync import TrackSyncService

session_path = "/app/session.session"
if not os.path.exists(session_path):
    tdata_path = "/app/tdata"
    if os.path.exists(tdata_path):
        convert_tdata_to_session.convert(session_path, tdata_path)
    else:
        raise RuntimeError("Telegram session not found in directory")
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
telegram_manager = TelethonTelegramManager(
    session_path, os.getenv("TELEGRAM_API_ID"), os.getenv("TELEGRAM_API_HASH")
)
telegram_manager.start()

spotify_auth = SpotifyAuth(
    os.getenv("SPOTIFY_CLIENT_ID"),
    os.getenv("SPOTIFY_CLIENT_SECRET"),
    os.getenv("SPOTIFY_REDIRECT_URI"),
    os.getenv("SPOTIFY_SCOPE") or "user-read-currently-playing",
)
spotify_manager = None
if os.getenv("SPOTIFY_REFRESH_TOKEN"):
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    token_info, spotify_manager = spotify_auth.from_refresh_token(
        os.getenv("SPOTIFY_REFRESH_TOKEN")
    )
    print(f"Authorized with refresh token: {refresh_token}", flush=True)
callback_server = SpotifyCallbackServer()
clean_tracks = (os.getenv("CLEAN_TRACKS") or "true").strip().lower() == "true"

threading.Thread(target=callback_server.start, daemon=True).start()


def load_backend_from_env():
    backend_path = (
        os.getenv("TRACKS_BACKEND") or "spotdl_track_backend.SpotdlTrackBackend"
    )
    full_backend_path = "backend." + backend_path
    module_path, class_name = full_backend_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    backend_class = getattr(module, class_name)
    return backend_class()


track_backend = load_backend_from_env()
default_track_backend = ZeroTrackBackend()
track_sync = TrackSyncService(
    telegram_manager,
    track_backend,
    default_track_backend,
    os.getenv("TRACKS_CACHE_SIZE") or 20,
)


def get_track(track_info):
    name = track_info["item"]["name"]
    artists = ", ".join(a["name"] for a in track_info["item"]["artists"])
    cover_url = track_info["item"]["album"]["images"][0]["url"]
    album = track_info["item"]["album"]["name"]
    spotify_url = track_info["item"]["external_urls"]["spotify"]

    track_number = track_info["item"]["track_number"]
    release_date = track_info["item"]["album"]["release_date"]
    year = release_date.split("-")[0]

    return Track(name, artists, cover_url, album, spotify_url, None, year, track_number)


while True:
    try:
        code = callback_server.get_code()
        if code is not None:
            token_info, spotify_manager = spotify_auth.exchange_code(code)
            print(
                f"Authorized with refresh token: {token_info.get('refresh_token')}",
                flush=True,
            )
            callback_server.set_code(None)
        if spotify_manager is not None:
            track_info = spotify_manager.current_user_playing_track()
            if track_info and track_info.get("item"):
                track = get_track(track_info)
                if track_sync.active_track != track:
                    track_sync.handle_track(track)
            else:
                track_sync.handle_no_track(clean_tracks)
        track_sync.process_ready_replacements()
    except Exception as e:
        print(f"Error occurred: {e}")
    time.sleep(0.5)
