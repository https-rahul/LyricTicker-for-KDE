import requests

def get_lyrics(artist, title):
    if not artist or not title:
        return "Spotify not running"
    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json().get("lyrics", "Lyrics not found")
    except:
        pass
    return "Lyrics not found"
