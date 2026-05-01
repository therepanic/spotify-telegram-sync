import os
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from lru_cache import LRUCache


@dataclass
class CachedTrackEntry:
    track: object
    message: object
    saved_music: object
    replacement_sequence: int | None = None
    replacement_state: str = "none"
    replacement_path: str | None = None


class TrackSyncService:
    def __init__(
        self, telegram_manager, track_backend, default_track_backend, cache_size
    ):
        self.telegram_manager = telegram_manager
        self.track_backend = track_backend
        self.default_track_backend = default_track_backend
        self.cached_tracks = LRUCache(cache_size)
        self.active_track = None
        self.download_executor = ThreadPoolExecutor(
            max_workers=self._get_download_workers()
        )
        self.replacement_queue = {}
        self.replacement_sequence = 0
        self.state_lock = threading.RLock()

    def handle_track(self, track):
        entry = self.cached_tracks.get(track)
        if entry is not None:
            self.active_track = track
            self.telegram_manager.save_music(entry.saved_music, True, None)
            self.telegram_manager.save_music(entry.saved_music, False, None)
            return

        entry = self._create_track_entry(track)
        if self.cached_tracks.is_full():
            self._evict_oldest_track()
        self.cached_tracks.put(track, entry)
        self.active_track = track
        self._schedule_replacement_if_supported(entry)

    def handle_no_track(self, clean_tracks):
        self.active_track = None
        if not clean_tracks:
            return

        while len(self.cached_tracks) > 0:
            _, entry = self.cached_tracks.pop_lru()
            self._mark_replacement_skipped(entry)
            self.telegram_manager.save_music(entry.saved_music, True, None)
            self.telegram_manager.delete_message("me", entry.message.id)

    def process_ready_replacements(self, limit=1):
        processed = 0
        while processed < limit:
            sequence, entry = self._next_replacement_entry()
            if entry is None:
                return

            if entry.replacement_state == "pending":
                return

            self.replacement_queue.pop(sequence, None)

            if entry.replacement_state == "ready":
                self._apply_replacement(entry)

            self._cleanup_replacement_file(entry)
            entry.replacement_state = "applied"
            processed += 1

    def _create_track_entry(self, track):
        temp_path = self._create_temp_mp3_path()
        try:
            if not self.track_backend.recreate(temp_path, track):
                self.default_track_backend.recreate(temp_path, track)

            uploaded_file = self.telegram_manager.upload_file(temp_path)
            message = self.telegram_manager.send_file("me", uploaded_file)
            saved_music = message.media.document
            self.telegram_manager.save_music(saved_music, False, None)
            return CachedTrackEntry(
                track=track, message=message, saved_music=saved_music
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _schedule_replacement_if_supported(self, entry):
        if not hasattr(self.track_backend, "create_replacement"):
            return

        sequence = self.replacement_sequence
        self.replacement_sequence += 1
        entry.replacement_sequence = sequence
        entry.replacement_state = "pending"
        self.replacement_queue[sequence] = entry
        self.download_executor.submit(self._prepare_replacement, entry)

    def _prepare_replacement(self, entry):
        temp_path = self._create_temp_mp3_path()
        try:
            result = self.track_backend.create_replacement(temp_path, entry.track)
            with self.state_lock:
                if entry.replacement_state == "skipped":
                    if result and os.path.exists(temp_path):
                        os.remove(temp_path)
                    return

                if result:
                    entry.replacement_path = temp_path
                    entry.replacement_state = "ready"
                else:
                    entry.replacement_state = "failed"
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        except Exception:
            with self.state_lock:
                entry.replacement_state = "failed"
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _apply_replacement(self, entry):
        current_entry = self.cached_tracks.peek(entry.track)
        if current_entry is not entry or not entry.replacement_path:
            return

        after_id = self._get_after_id(entry.track)
        uploaded_file = self.telegram_manager.upload_file(entry.replacement_path)
        message = self.telegram_manager.send_file("me", uploaded_file)
        saved_music = message.media.document
        self.telegram_manager.save_music(saved_music, False, after_id)
        self.telegram_manager.save_music(entry.saved_music, True, None)
        self.telegram_manager.delete_message("me", entry.message.id)
        entry.message = message
        entry.saved_music = saved_music

    def _get_after_id(self, track):
        keys = self.cached_tracks.keys()
        try:
            index = keys.index(track)
        except ValueError:
            return None

        if index == len(keys) - 1:
            return None

        next_track = keys[index + 1]
        next_entry = self.cached_tracks.peek(next_track)
        if next_entry is None:
            return None
        return next_entry.saved_music

    def _evict_oldest_track(self):
        _, entry = self.cached_tracks.pop_lru()
        self._mark_replacement_skipped(entry)
        self.telegram_manager.save_music(entry.saved_music, True, None)
        self.telegram_manager.delete_message("me", entry.message.id)

    def _mark_replacement_skipped(self, entry):
        if entry.replacement_state != "pending":
            return
        entry.replacement_state = "skipped"

    def _next_replacement_entry(self):
        if not self.replacement_queue:
            return None, None

        sequence = min(self.replacement_queue)
        return sequence, self.replacement_queue[sequence]

    def _cleanup_replacement_file(self, entry):
        if entry.replacement_path and os.path.exists(entry.replacement_path):
            os.remove(entry.replacement_path)
        entry.replacement_path = None

    def _create_temp_mp3_path(self):
        handle, path = tempfile.mkstemp(suffix=".mp3")
        os.close(handle)
        return path

    def _get_download_workers(self):
        raw_value = os.getenv("TRACKS_DOWNLOAD_WORKERS", "2")
        try:
            return max(1, int(raw_value))
        except ValueError:
            return 2
