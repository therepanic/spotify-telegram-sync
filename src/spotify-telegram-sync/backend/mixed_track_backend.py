from backend.spotdl_track_backend import SpotdlTrackBackend
from backend.zero_track_backend import ZeroTrackBackend


class MixedTrackBackend:
    def __init__(self):
        self.zero_backend = ZeroTrackBackend()
        self.spotdl_backend = SpotdlTrackBackend()

    def recreate(self, temp_path, track):
        return self.zero_backend.recreate(temp_path, track)

    def create_replacement(self, temp_path, track):
        return self.spotdl_backend.recreate(temp_path, track)
