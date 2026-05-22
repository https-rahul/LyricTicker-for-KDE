# backend/lyrics/lrclib.py
import aiohttp
import logging
from backend.lyrics.base import BaseLyricsProvider
from backend.models import TrackData

logger = logging.getLogger(__name__)

class LRCLibProvider(BaseLyricsProvider):

    BASE_URL = "https://lrclib.net/api/get"
    HEADERS = {
        "User-Agent": "LyricTicker/0.1.0 (https://github.com/rahulgaur104/lyricticker)",
        "Accept": "application/json"
    }

    @property
    def name(self) -> str:
        return "LRCLib"

    async def fetch_lyrics(self, track: TrackData) -> str | None:
        if track.player is None:
            return None

        params = {
            "artist_name": track.artist,
            "track_name": track.title,
            "album_name": track.album,
            "duration": track.duration
        }

        try:
            logger.info(f"[{self.name}] Searching: {track.artist} - {track.title}")
            async with aiohttp.ClientSession(headers=self.HEADERS) as session:
                async with session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 404:
                        logger.warning(f"[{self.name}] Not found")
                        return None
                    response.raise_for_status()
                    data = await response.json()

                    synced = data.get("syncedLyrics")
                    if synced:
                        logger.info(f"[{self.name}] ✓ Synced lyrics found")
                        return synced

                    logger.warning(f"[{self.name}] No synced lyrics available")
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"[{self.name}] Request failed: {e}")
            return None