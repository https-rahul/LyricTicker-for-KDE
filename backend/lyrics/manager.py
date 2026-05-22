# backend/lyrics/manager.py
import logging
from backend.lyrics.base import BaseLyricsProvider
from backend.lyrics.lrclib import LRCLibProvider
from backend.models import TrackData

logger = logging.getLogger(__name__)

class LyricsManager:
    """
    Tries each lyrics source in priority order.
    Returns the first synced result found, or None if all sources fail.
    Adding a new source = add it to self.sources. Nothing else changes.
    """

    def __init__(self):
        self.sources: list[BaseLyricsProvider] = [
            LRCLibProvider(),
            # NetEaseProvider(),   ← uncomment when ready
            # QQMusicProvider(),
            # KugouProvider(),
        ]

    async def fetch_lyrics(self, track: TrackData) -> str | None:
        for source in self.sources:
            try:
                result = await source.fetch_lyrics(track)
                if result:
                    logger.info(f"✓ Lyrics found via {source.name}")
                    return result
                logger.info(f"✗ {source.name} had no result, trying next...")
            except Exception as e:
                logger.error(f"✗ {source.name} failed with error: {e}, trying next...")
                continue

        logger.warning("All lyrics sources exhausted — no synced lyrics found")
        return None