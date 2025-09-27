import os
import shutil
import glob
import subprocess
import time
from backend.track_backend import TrackBackend

temp_audio_path = "/app/audio"
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

class SpotdlTrackBackend(TrackBackend):
    def recreate(self, temp_path, track):
        os.makedirs(temp_audio_path, exist_ok=True)
        cmd = [
            "spotdl", "download",
            track.spotify_url,
            "--output", temp_audio_path,
            "--client-id", client_id,
            "--client-secret", client_secret
        ]
        try:
            subprocess.run(cmd, check=True, timeout=60)
        except subprocess.TimeoutExpired:
            return None
        temp_file = None
        for _ in range(10):
            mp3_files = glob.glob(os.path.join(temp_audio_path, "*.mp3"))
            if mp3_files:
                temp_file = mp3_files[0]
                break
            time.sleep(0.5)
        if not temp_file:
            return None
        shutil.move(temp_file, temp_path)
        return temp_path
