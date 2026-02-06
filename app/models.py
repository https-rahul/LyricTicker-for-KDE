from dataclasses import dataclass
from typing import Optional

@dataclass
class TrackData:
    player: str
    title: str
    artist: str
    album: str
    duration: float
    position: float
    status: str

    @classmethod
    def empty(cls):
        return cls("None", "Unknown", "Unknown", "Unknown", 0.0, 0.0, "Stopped")
