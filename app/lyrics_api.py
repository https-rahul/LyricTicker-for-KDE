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

    # Added missing '&' before track_name
    url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={title}&album_name={album}&duration={duration}"

    try:
        logging.info(f"Hitting the LRCLIB API for: {title}")
        r = requests.get(url)

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