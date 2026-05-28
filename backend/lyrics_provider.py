import os
import re
import asyncio
import logging
from PySide6.QtCore import QObject, Signal, Property, QTimer
from backend.models import TrackData
from backend.mpris_service import MPRISService
from backend.lyrics.manager import LyricsManager
from backend.constants import CACHE_FILE

logger = logging.getLogger(__name__)
CACHE_FILE = os.path.expanduser(CACHE_FILE)

class LyricsProvider(QObject):
    lyricsLinesChanged = Signal()
    currentIndexChanged = Signal()

    def __init__(self, mpris_service: MPRISService, lyrics_manager: LyricsManager):
        super().__init__()
        self.mpris = mpris_service
        self.lyrics_api = lyrics_manager

        self._lyrics_lines = []
        self._timestamped_lyrics = []
        self._current_index = -1
        self._current_lyric = ""
        self._last_track_id = ""
        self._last_cached_lyric = ""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_state)
        self._fetch_task = None

    def update_state(self):
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._async_update_wrapper())
            task.add_done_callback(self._handle_task_result)
        except Exception as e:
            logger.error(f"Timer failed to schedule task: {e}")

    def _handle_task_result(self, task):
        try:
            task.result()
        except Exception as e:
            logger.error(f"Task error: {e}")

    async def _async_update_wrapper(self):
        try:
            track = await self.mpris.get_current_track()
            if track.player is not None and track.status == "Playing":  # ← audit fix #1
                self.sync_logic(track)
        except Exception as e:
            logger.error(f"Error in wrapper: {e}")

    def sync_logic(self, track: TrackData):
        current_track_id = f"{track.artist}-{track.title}"
        if current_track_id != self._last_track_id:
            logger.info(f"New song detected: {current_track_id}")
            self._last_track_id = current_track_id

            self._timestamped_lyrics = []
            self._lyrics_lines = []
            self._current_index = -1
            self._current_lyric = ""
            self.currentIndexChanged.emit()
            self.lyricsLinesChanged.emit()

            if self._fetch_task and not self._fetch_task.done():
                self._fetch_task.cancel()
                logger.debug("Cancelled previous fetch task")

            loop = asyncio.get_event_loop()
            self._fetch_task = loop.create_task(self.fetch_new_song_lyrics(track))
            return

        if not self._timestamped_lyrics:
            return

        new_index = self._current_index
        for i, (ts, text) in enumerate(self._timestamped_lyrics):
            if track.position >= ts:
                new_index = i
            else:
                break

        if new_index != self._current_index and new_index >= 0:
            self._current_index = new_index
            self._current_lyric = self._timestamped_lyrics[new_index][1]
            self.currentIndexChanged.emit()
            self._write_to_cache(self._current_lyric)

    async def fetch_new_song_lyrics(self, track: TrackData):
        try:
            raw_lyrics = await self.lyrics_api.fetch_lyrics(track)

            if raw_lyrics:
                parsed = self.parse_synced_lyrics(raw_lyrics)
                if parsed:
                    self._timestamped_lyrics = parsed
                    self._lyrics_lines = [l for _, l in self._timestamped_lyrics]
                    logger.info("✓ Synced lyrics loaded successfully")
                else:
                    logger.warning("Lyrics returned but no timestamps found — skipping")
                    self._timestamped_lyrics = []
                    self._lyrics_lines = []

                self.lyricsLinesChanged.emit()
                self.sync_logic(track)
            else:
                self._current_lyric = ""
                self._current_index = -1
                self.currentIndexChanged.emit()
                self._write_to_cache(self._current_lyric)

        except asyncio.CancelledError:
            logger.debug(f"Fetch cancelled for {track.artist}-{track.title}")
            return

        except Exception as e:
            logger.error(f"Failed to fetch lyrics: {e}")

    def parse_synced_lyrics(self, synced_lyrics):
        if not synced_lyrics or not isinstance(synced_lyrics, str):
            return []

        pattern = re.compile(r"\[(\d{2}):(\d{2}(?:\.\d+)?)]\s*(.*)")
        result = []
        for line in synced_lyrics.split("\n"):
            match = pattern.match(line.strip())
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                total_seconds = minutes * 60 + seconds
                text = match.group(3).strip()
                result.append((total_seconds, text))

        result.sort(key=lambda x: x[0])
        return result

    def _write_to_cache(self, text: str):
        try:
            if text == self._last_cached_lyric:
                return
            self._last_cached_lyric = text
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(text.strip())
        except Exception as e:
            logger.error(f"Failed to write lyric cache: {e}")

    @Property(list, notify=lyricsLinesChanged)
    def lyrics_lines(self):
        return self._lyrics_lines

    @Property(int, notify=currentIndexChanged)
    def current_index(self):
        return self._current_index

    @Property(str, notify=currentIndexChanged)
    def current_lyric(self):
        return self._current_lyric

    def clear(self):
        self._current_lyric = ""
        self._current_index = -1
        self._last_cached_lyric = ""
        self._write_to_cache("")
        self.currentIndexChanged.emit()