import requests
import logging

# Basic configuration to make sure logs actually show up
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_lyrics(artist, title, album, duration):
    if not artist or not title:
        logging.warning("Artist or Title missing. Spotify might not be running.")
        return "Spotify not running"
    else:
        logging.info(f"Track Found with metadata -- artist name: {artist} and title: {title} and album: {album} duration: {duration}")

    url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={title}&album_name={album}&duration={duration}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64",
        "Accept":"application/json",
        "Connection": "close"
    }
    try:
        logging.info(f"Hitting the LRCLIB API for: {title}")
        r = requests.get(url, timeout=(3, 10))
        r.raise_for_status()


        if r.status_code == 200:
            logging.info("API request successful.")
            # .get() is safer here to avoid KeyErrors
            return r.json().get("syncedLyrics", "Lyrics not found")
        else:
            # Fixed the formatting syntax here
            logging.error(f"Non-200 Status Code: {r.status_code} and actual response: {r.json}")

    except requests.exceptions.RequestException as e:
        # This captures the specific error and logs the full traceback
        logging.exception("An error occurred during the API request")

    return "Lyrics not found"