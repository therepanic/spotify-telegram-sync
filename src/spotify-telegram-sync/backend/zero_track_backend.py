import shutil
import os
import requests
from backend.track_backend import TrackBackend
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC, TALB

SILENCE_MP3 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "silence.mp3"))

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

class ZeroTrackBackend(TrackBackend):
    def recreate(self, temp_path, track):
        shutil.copyfile(SILENCE_MP3, temp_path)
        apply_track_info(temp_path, track)
        return temp_path
