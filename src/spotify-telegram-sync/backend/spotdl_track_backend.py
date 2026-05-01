import os
import shutil
import glob
import subprocess
import time
import tempfile
from backend.track_backend import TrackBackend

temp_audio_root = "/app/audio"
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")


class SpotdlTrackBackend(TrackBackend):
    def recreate(self, temp_path, track):
        os.makedirs(temp_audio_root, exist_ok=True)
        temp_audio_path = tempfile.mkdtemp(prefix="spotdl-", dir=temp_audio_root)
        cmd = [
            "spotdl",
            "download",
            track.spotify_url,
            "--output",
            temp_audio_path,
            "--client-id",
            client_id,
            "--client-secret",
            client_secret,
        ]
        try:
            subprocess.run(cmd, check=True, timeout=60)
        except subprocess.TimeoutExpired:
            shutil.rmtree(temp_audio_path, ignore_errors=True)
            return None
        except subprocess.CalledProcessError:
            shutil.rmtree(temp_audio_path, ignore_errors=True)
            return None
        temp_file = None
        for _ in range(10):
            mp3_files = glob.glob(os.path.join(temp_audio_path, "*.mp3"))
            if mp3_files:
                temp_file = mp3_files[0]
                break
            time.sleep(0.5)
        if not temp_file:
            shutil.rmtree(temp_audio_path, ignore_errors=True)
            return None
        shutil.move(temp_file, temp_path)
        shutil.rmtree(temp_audio_path, ignore_errors=True)
        return temp_path
