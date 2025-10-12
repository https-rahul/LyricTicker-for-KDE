from pydbus import SessionBus

def get_current_track():
    bus = SessionBus()
    try:
        spotify = bus.get("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
        metadata = spotify.Metadata
        artist = metadata.get("xesam:artist")[0] if metadata.get("xesam:artist") else "Unknown"
        title = metadata.get("xesam:title") if metadata.get("xesam:title") else "Unknown"

        return artist, title
    except Exception:
        return None, None
