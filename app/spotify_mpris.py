import requests
import logging
from pydbus import SessionBus

# 1. Configure Logging
# level=logging.DEBUG will show EVERYTHING. Change to logging.INFO for less clutter.
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_current_track():
    bus = SessionBus()
    try:
        # Connect to the Spotify player interface
        spotify = bus.get("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")

        # 1. Get Metadata (Static info)
        metadata = spotify.Metadata
        artists = metadata.get("xesam:artist", ["Unknown"])
        artist = artists[0] if artists else "Unknown"
        title = metadata.get("xesam:title", "Unknown")
        album = metadata.get("xesam:album", "Unknown")
        duration = int(metadata.get("mpris:length", 0) / 1000000)

        # 2. Get Position (Dynamic info - current time in seconds)
        # MPRIS returns position in microseconds
        position = int(spotify.Position / 1000000)

        return artist, title, album, duration, position

    except Exception:
        return None, None, None, None, 0


def get_lyrics(artist, title, album, duration):
    if not artist or not title:
        logging.error("Incomplete track info provided to get_lyrics.")
        return "Track info missing"

    url = "https://lrclib.net/api/get"

    # Using 'params' is better than f-strings for URLs; it handles encoding automatically
    query_params = {
        "artist_name": artist,
        "track_name": title,
        "album_name": album,
        "duration": duration
    }

    try:
        logging.info(f"Requesting lyrics from LRCLIB for '{title}'...")
        logging.debug(f"API Params: {query_params}")

        r = requests.get(url, params=query_params, timeout=10)

        if r.status_code == 200:
            logging.info("Lyrics successfully retrieved.")
            data = r.json()
            return data.get("syncedLyrics") or data.get("plainLyrics") or "Lyrics empty in database"

        elif r.status_code == 404:
            logging.warning(f"Lyrics not found for: {title} (404)")
        else:
            logging.error(f"API Error. Status Code: {r.status_code} | Response: {r.text}")

    except requests.exceptions.RequestException:
        logging.exception("A network error occurred while hitting the LRCLIB API")

    return "Lyrics not found"

# --- Main Execution ---
if __name__ == "__main__":
    art, tit, alb, dur = get_current_track()
    if art:
        lyrics = get_lyrics(art, tit, alb, dur)
        # Final output or further processing