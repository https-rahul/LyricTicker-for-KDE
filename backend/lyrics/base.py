# backend/lyrics/base.py
from abc import ABC, abstractmethod
from backend.models import TrackData


class BaseLyricsProvider(ABC):
    """
    Abstract base class for all lyrics sources.
    Every source (LRCLib, NetEase, QQ Music, Kugou) must implement this.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human readable name e.g. 'LRCLib'"""
        raise NotImplementedError

    @abstractmethod
    async def fetch_lyrics(self, track: TrackData) -> str | None:
        """
        Fetch synced lyrics for a track.
        Returns LRC formatted string if found, None if not found.
        Must only return synced lyrics — plain text is rejected by manager.
        """
        raise NotImplementedError