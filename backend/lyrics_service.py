import requests
import logging

logger = logging.getLogger(__name__)

class LyricsService:
    def __init__(self):
        self.base_url = "https://lrclib.net/api/get"
        self.session = requests.Session()  # Industry standard: reuse connections
        self.session.headers.update({
            "User-Agent": "LyricTicker/1.0 (Linux; Project)",
            "Accept": "application/json"
        })

    def fetch_lyrics(self, track) -> str:

        if track.player == "None":
            return "No player active"

        params = {
            "artist_name": track.artist,
            "track_name": track.title,
            "album_name": track.album,
            "duration": track.duration
        }

        try:
            logger.info(f"Searching lyrics for: {track.artist} - {track.title}")
            response = self.session.get(self.base_url, params=params, timeout=10)

            if response.status_code == 404:
                logger.warning("Lyrics not found on LRCLIB.")
                return "Lyrics not found"

            response.raise_for_status()
            data = response.json()

            return data.get("syncedLyrics") or data.get("plainLyrics") or "Lyrics not found"

        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            return "Error fetching lyrics"