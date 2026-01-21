from PySide6.QtCore import QObject, Signal, Property, QTimer, Slot

from . import spotify_mpris
from . import lyrics_api

class LyricsProvider(QObject):
    # Signals must be defined before usage in Property decorators
    lyricsLinesChanged = Signal()
    currentIndexChanged = Signal()

    @Property(str, notify=currentIndexChanged)
    def current_lyric(self):
        return self._current_lyric

    def __init__(self):
        super().__init__()
        self._lyrics_lines = []
        self._timestamped_lyrics = []  # List of (seconds, lyric)
        self._current_index = 0
        self._current_lyric = ""
        self._last_track_id = ""

        self.timer = QTimer()
        self.timer.timeout.connect(self.sync_logic)
        self.timer.start(200)

    def sync_logic(self):
        # 1. Get current state from Spotify
        artist, title, album, duration, position = spotify_mpris.get_current_track()

        if not artist:
            return

        current_track_id = f"{artist}-{title}"
        if current_track_id != self._last_track_id:
            self._last_track_id = current_track_id
            self.fetch_new_song_lyrics(artist, title, album, duration)

        new_index = 0
        for i, (ts, text) in enumerate(self._timestamped_lyrics):
            if position >= ts:
                new_index = i
            else:
                break
        if new_index != self._current_index:
            self._current_index = new_index
            self._current_lyric = self._timestamped_lyrics[new_index][1] if self._timestamped_lyrics else ""
            self.currentIndexChanged.emit()

    def fetch_new_song_lyrics(self, artist, title, album, duration):
        # This only runs once per song
        raw_lyrics = lyrics_api.get_lyrics(artist, title, album, duration)
        self._timestamped_lyrics = self.parse_synced_lyrics(raw_lyrics)
        self._lyrics_lines = [l for _, l in self._timestamped_lyrics]
        self.lyricsLinesChanged.emit()

    def parse_synced_lyrics(self, synced_lyrics):
        import re
        pattern = re.compile(r"\[(\d{2}):(\d{2}\.\d{2})\] (.*)")
        result = []
        for line in synced_lyrics.split("\n"):
            match = pattern.match(line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                total_seconds = minutes * 60 + seconds
                lyric = match.group(3)
                result.append((total_seconds, lyric))
        return result

    #  Improvement 2: Use the new lyricsLinesChanged signal
    @Property(list, notify=lyricsLinesChanged) 
    def lyrics_lines(self):
        return self._lyrics_lines

    #  Improvement 3: Use the new currentIndexChanged signal
    @Property(int, notify=currentIndexChanged) 
    def current_index(self):
        return self._current_index

    def update_lyrics(self):
        artist, title, album, duration = spotify_mpris.get_current_track()
        synced_lyrics = lyrics_api.get_lyrics(artist, title, album, duration)
        # Parse synced lyrics
        timestamped = self.parse_synced_lyrics(synced_lyrics)
        self._timestamped_lyrics = timestamped
        self._lyrics_lines = [lyric for _, lyric in timestamped]
        # Default to first lyric line
        if timestamped:
            self._current_index = 0
            self._current_lyric = timestamped[0][1]
        else:
            self._current_index = 0
            self._current_lyric = ""
        self.lyricsLinesChanged.emit()
        self.currentIndexChanged.emit()

    @Slot()
    def next_line(self):
        if self._current_index < len(self._timestamped_lyrics) - 1:
            self._current_index += 1
            self._current_lyric = self._timestamped_lyrics[self._current_index][1]
            self.currentIndexChanged.emit()