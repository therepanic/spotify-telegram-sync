import os
import shutil
import threading
import time
import requests
from spotify_callback_server import SpotifyCallbackServer
from spotify_auth import SpotifyAuth
from telethon_telegram_manager import TelethonTelegramManager
from track import Track
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC, TALB
from lru_cache import LRUCache

spotify_auth = SpotifyAuth()
spotify_manager = None
callback_server = SpotifyCallbackServer()

SILENCE_MP3 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "silence.mp3")
sess_path = "/app/session.session"
telegram_manager = TelethonTelegramManager(sess_path, os.getenv("TELEGRAM_API_ID"), os.getenv("TELEGRAM_API_HASH"))
telegram_manager.start()

active_track = None
cached_tracks = LRUCache(os.getenv("TRACKS_CACHE_SIZE") or 20)

threading.Thread(target=callback_server.start, daemon=True).start()

def get_track(track_info):
    name = track_info["item"]["name"]
    artists = ", ".join(a["name"] for a in track_info["item"]["artists"])
    cover_url = track_info["item"]["album"]["images"][-1]["url"]
    album = track_info["item"]["album"]["name"]

    return Track(name, artists, cover_url, album)

def apply_track_info(file_path, track):
    audio = MP3(file_path, ID3=ID3)
    if audio.tags is None:
        audio.add_tags()
    audio.tags["TIT2"] = TIT2(encoding=3, text=track.name)
    audio.tags["TPE1"] = TPE1(encoding=3, text=track.artists)
    audio.tags["TALB"] = TALB(encoding=3, text=track.album)

    cover_bytes = requests.get(track.cover_url).content

    audio.tags["APIC"] = APIC(
        encoding=3,
        mime="image/jpeg",
        type=3,
        desc="Cover",
        data=cover_bytes
    )
    audio.save(v2_version=3)

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
                        temp_path = "/app/tempFile.mp3"
                        shutil.copyfile(SILENCE_MP3, temp_path)
                        apply_track_info(temp_path, track)

                        uploaded_file = telegram_manager.upload_file(temp_path)

                        msg = telegram_manager.send_file("me", uploaded_file)
                        telegram_manager.save_music(msg.media.document, None, None)

                        active_track = track

                        if (cached_tracks.is_full()):
                            old_track, (old_uploaded_file, old_msg) = cached_tracks.pop_lru()
                            telegram_manager.save_music(old_msg, True, None)
                            telegram_manager.delete_message("me", old_msg.id)

                        cached_tracks.put(track, (uploaded_file, msg))
                        os.remove(temp_path)
            else:
                #TODO no track logic 
                pass
    except Exception as e:
        print(f"Error occurred: {e}")
    time.sleep(0.5)
