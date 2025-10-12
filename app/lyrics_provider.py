from PySide6.QtCore import QObject, Signal, Property, QTimer, Slot

from . import spotify_mpris
from . import lyrics_api

class LyricsProvider(QObject):
    # ⭐️ Improvement 1: Separate Signals for targeted updates
    lyricsLinesChanged = Signal()
    currentIndexChanged = Signal() 

    def __init__(self):
        super().__init__()
        self._lyrics_lines = []
        self._current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_lyrics)
        self.timer.start(5000)

    # ⭐️ Improvement 2: Use the new lyricsLinesChanged signal
    @Property(list, notify=lyricsLinesChanged) 
    def lyrics_lines(self):
        return self._lyrics_lines

    # ⭐️ Improvement 3: Use the new currentIndexChanged signal
    @Property(int, notify=currentIndexChanged) 
    def current_index(self):
        return self._current_index

    def update_lyrics(self):
        artist, title = spotify_mpris.get_current_track()
        lyrics_text = lyrics_api.get_lyrics(artist, title)
        lines = lyrics_text.split("\n")
        
        if lines != self._lyrics_lines:
            self._lyrics_lines = lines
            self._current_index = 0
            
            # Emit both signals, as both properties have changed
            self.lyricsLinesChanged.emit() 
            self.currentIndexChanged.emit()

    @Slot()
    def next_line(self):
        if self._current_index < len(self._lyrics_lines) - 1:
            self._current_index += 1
            
            # Emit ONLY the currentIndexChanged signal
            self.currentIndexChanged.emit()