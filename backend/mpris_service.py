import logging
from typing import Optional
from dbus_next.signature import Variant
from backend.models import TrackData

logger = logging.getLogger(__name__)

class MPRISService:
    def __init__(self, bus):
        self.bus = bus

    def _unwrap(self, value):
        if isinstance(value, Variant):
            return value.value
        return value

    async def get_current_track(self) -> TrackData:
        try:
            #all players
            reply = await self.bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
            dbus_proxy = self.bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus', reply)
            dbus_iface = dbus_proxy.get_interface('org.freedesktop.DBus')
            names = await dbus_iface.call_list_names()
            players = [n for n in names if n.startswith('org.mpris.MediaPlayer2')]

            for name in players:
                track = await self._query_player(name)
                if track and track.status == "Playing":
                    return track

            return TrackData.empty()
        except Exception as e:
            logger.error(f"MPRIS Service Error: {e}")
            return TrackData.empty()

    async def _query_player(self, name: str) -> Optional[TrackData]:
        try:
            # for both Spotify and Chrome
            from dbus_next import Message
            msg = Message(
                destination=name,
                path='/org/mpris/MediaPlayer2',
                interface='org.freedesktop.DBus.Properties',
                member='GetAll',
                signature='s',
                body=['org.mpris.MediaPlayer2.Player']
            )
            reply = await self.bus.call(msg)
            props = reply.body[0] if reply.body else {}

            status = self._unwrap(props.get('PlaybackStatus', 'Stopped'))
            if status != "Playing":
                return None

            meta = self._unwrap(props.get('Metadata', {}))
            pos = self._unwrap(props.get('Position', 0))

            artists = self._unwrap(meta.get('xesam:artist', ['Unknown']))
            artist = artists[0] if isinstance(artists, list) and artists else "Unknown"

            PLAYER_NAMES = {
                "spotify": "Spotify",
                "firefox": "Firefox",
                "chromium": "Chromium",
                "brave": "Brave",
                "vlc": "VLC",
                "fooyin": "Fooyin",
                "elisa": "Elisa",
            }
            raw = name.split('.')[-1].lower()
            player_display = PLAYER_NAMES.get(raw, raw.capitalize())

            return TrackData(
                player=player_display,
                title=self._unwrap(meta.get('xesam:title', 'Unknown')),
                artist=artist,
                album=self._unwrap(meta.get('xesam:album', 'Unknown')),
                duration=self._unwrap(meta.get('mpris:length', 0)) / 1_000_000,
                position=pos / 1_000_000,
                status=status
            )
        except Exception as e:
            logger.debug(f"Could not query MPRIS service for player:{name} {e}")
            return None