from abc import ABC, abstractmethod
from backend.models import TrackData

class BaseLyricsProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fetch_lyrics(self, track: TrackData) -> str | None:
        raise NotImplementedError