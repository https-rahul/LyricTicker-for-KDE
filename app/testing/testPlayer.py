import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Configure logging with timestamps and detailed info
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Calculate the path to the 'LyricTicker' directory (two levels up from this file)
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Now these imports will work regardless of how you run the script
import asyncio
from dbus_next.aio import MessageBus
from dbus_next import Message
from app.models import TrackData # Changed from ..models to app.models


class MPRISService:
    def __init__(self):
        self.bus = None
        logger.info("MPRISService initialized")

    async def connect(self):
        """Standard practice: Connect once and reuse the bus."""
        logger.info("Attempting to connect to DBus...")
        
        if not self.bus:
            try:
                self.bus = await MessageBus().connect()
                logger.info("✓ Successfully connected to DBus")
            except Exception as e:
                logger.error(f"✗ Failed to connect to DBus: {e}", exc_info=True)
                raise
        else:
            logger.debug("DBus connection already established, reusing...")
        
        return self.bus

    async def get_current_track(self) -> TrackData:
        logger.info("=" * 70)
        logger.info("Starting get_current_track() - Searching for playing media...")
        logger.info("=" * 70)
        
        try:
            bus = await self.connect()

            # 1. Get all players on the bus
            logger.debug("Step 1: Fetching introspection data for DBus...")
            reply = await bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
            logger.debug(f"✓ Introspection successful")

            # Find player names (e.g., org.mpris.MediaPlayer2.vlc)
            logger.debug("Step 2: Listing all MPRIS media players on the system...")
            player_names = list(await self._list_mpris_players(bus))
            
            if not player_names:
                logger.warning("✗ No MPRIS-compliant media players found on the system")
                logger.info("Available players could include: Spotify, VLC, YouTube Music, MPD, etc.")
                return TrackData.empty()
            
            logger.info(f"✓ Found {len(player_names)} MPRIS player(s): {player_names}")

            # 2. Iterate through each player
            for idx, name in enumerate(player_names, 1):
                player_display_name = name.split('.')[-1].upper()
                logger.info(f"\n[{idx}/{len(player_names)}] Checking player: {player_display_name}")
                logger.debug(f"  Full DBus name: {name}")
                
                try:
                    # First try the standard interface-based approach (works for Spotify, VLC, etc.)
                    logger.debug(f"  [Method 1] Trying standard interface approach...")
                    track_data = await self._try_standard_interface(bus, name, player_display_name)
                    if track_data and track_data.player != "None":
                        return track_data
                    
                    # If that fails, try the Properties-based approach (works for Brave/Chromium)
                    logger.debug(f"  [Method 2] Trying Properties.GetAll approach...")
                    track_data = await self._try_properties_approach(bus, name, player_display_name)
                    if track_data and track_data.player != "None":
                        return track_data
                        
                except Exception as e:
                    logger.warning(f"  ✗ Error checking player {player_display_name}: {e}", exc_info=True)
                    continue

            logger.warning("No currently playing media found on any player")
            return TrackData.empty()
            
        except Exception as e:
            logger.error(f"✗ Critical error in get_current_track(): {e}", exc_info=True)
            return TrackData.empty()

    async def _try_standard_interface(self, bus, name: str, player_display_name: str) -> TrackData:
        """Try to get track data using standard MPRIS interface methods"""
        try:
            # Get proxy objects - need introspection first
            logger.debug(f"    Getting introspection for {name}...")
            try:
                obj_introspection = await bus.introspect(name, '/org/mpris/MediaPlayer2')
                logger.debug(f"    ✓ Got introspection at /org/mpris/MediaPlayer2")
            except Exception as e:
                logger.debug(f"    Could not introspect {name}: {e}")
                return TrackData.empty()
            
            # Log available interfaces
            available_interfaces = [i.name for i in obj_introspection.interfaces]
            logger.debug(f"    Available interfaces from introspection: {available_interfaces}")
            
            if not available_interfaces:
                logger.debug(f"    No interfaces in introspection (likely Brave/Chromium)")
                return TrackData.empty()
            
            logger.debug(f"    Getting proxy object for {name}...")
            obj = bus.get_proxy_object(name, '/org/mpris/MediaPlayer2', obj_introspection)
            
            # Get Player interface
            try:
                player = obj.get_interface('org.mpris.MediaPlayer2.Player')
                properties = obj.get_interface('org.freedesktop.DBus.Properties')
                logger.debug(f"    ✓ Got Player interface")
            except Exception as e:
                logger.debug(f"    Could not get Player interface: {e}")
                return TrackData.empty()

            # Check Playback Status
            logger.debug(f"    Checking playback status...")
            try:
                status = await player.get_playback_status()
                logger.info(f"  Playback Status: {status}")
            except Exception as e:
                logger.warning(f"  Could not get playback status: {e}")
                status = "Unknown"
            
            if status != 'Playing':
                logger.debug(f"  → Player not playing (Status: {status}). Skipping...")
                return TrackData.empty()

            # Get Metadata
            logger.debug(f"  Retrieving track metadata...")
            metadata = await player.get_metadata()
            logger.debug(f"  ✓ Metadata retrieved. Raw metadata keys: {list(metadata.keys())}")
            
            # Log all available metadata for debugging
            if metadata:
                logger.debug(f"  === Full Metadata Debug ===")
                for key, value in metadata.items():
                    logger.debug(f"    {key}: {value}")
                logger.debug(f"  === End Metadata Debug ===")
            
            # Extract metadata with detailed logging and Variant unwrapping
            artist = metadata.get('xesam:artist', ['Unknown'])
            artist = self._unwrap_variant(artist)
            artist_str = artist[0] if isinstance(artist, list) and artist else "Unknown"
            logger.info(f"  Artist: {artist_str}")
            
            title = metadata.get('xesam:title', 'Unknown')
            title = self._unwrap_variant(title)
            logger.info(f"  Title: {title}")
            
            album = metadata.get('xesam:album', 'Unknown')
            album = self._unwrap_variant(album)
            logger.info(f"  Album: {album}")
            
            duration_us = metadata.get('mpris:length', 0)
            duration_us = self._unwrap_variant(duration_us)
            duration_sec = int(duration_us / 1_000_000) if duration_us else 0
            logger.info(f"  Duration: {duration_sec}s ({self._format_time(duration_sec)})")
            
            # Get Position
            logger.debug(f"  Getting playback position...")
            try:
                position_us = await properties.call_get('org.mpris.MediaPlayer2.Player', 'Position')
                position_us = self._unwrap_variant(position_us)
                position_sec = int(position_us / 1_000_000)
                logger.info(f"  Position: {position_sec}s ({self._format_time(position_sec)}) / {duration_sec}s")
            except Exception as e:
                logger.warning(f"  Could not get position: {e}")
                position_sec = 0

            # Log additional metadata if available
            url = metadata.get('xesam:url', 'N/A')
            url = self._unwrap_variant(url)
            logger.debug(f"  URL: {url}")
            
            genre = metadata.get('xesam:genre', [])
            genre = self._unwrap_variant(genre)
            if genre:
                genre_str = genre[0] if isinstance(genre, list) else genre
                logger.debug(f"  Genre: {genre_str}")
            
            track_id = metadata.get('mpris:trackid', 'N/A')
            track_id = self._unwrap_variant(track_id)
            logger.debug(f"  Track ID: {track_id}")
            
            # Create and return TrackData
            track_data = TrackData(
                artist=artist_str,
                title=title,
                album=album,
                duration=duration_sec,
                position=position_sec,
                player=player_display_name
            )
            
            logger.info("=" * 70)
            logger.info(f"✓ FOUND PLAYING TRACK - Player: {player_display_name}")
            logger.info("=" * 70)
            
            return track_data
            
        except Exception as e:
            logger.debug(f"  Standard interface approach failed: {e}")
            return TrackData.empty()

    async def _try_properties_approach(self, bus, name: str, player_display_name: str) -> TrackData:
        """Try to get track data using Properties.GetAll (for Brave/Chromium players)"""
        try:
            from dbus_next import Message
            
            logger.debug(f"    Attempting to get all properties for org.mpris.MediaPlayer2.Player...")
            
            # Call GetAll on Properties interface
            msg = Message(
                destination=name,
                path='/org/mpris/MediaPlayer2',
                interface='org.freedesktop.DBus.Properties',
                member='GetAll',
                signature='s',
                body=['org.mpris.MediaPlayer2.Player']
            )
            
            reply = await bus.call(msg)
            properties = reply.body[0] if reply.body else {}
            logger.debug(f"    ✓ Got {len(properties)} properties")
            
            # Extract playback status
            status_var = properties.get('PlaybackStatus')
            status = self._unwrap_variant(status_var) if status_var else "Unknown"
            logger.info(f"  Playback Status: {status}")
            
            if status != 'Playing':
                logger.debug(f"  → Player not playing (Status: {status}). Skipping...")
                return TrackData.empty()
            
            # Extract metadata
            metadata_var = properties.get('Metadata')
            metadata = self._unwrap_variant(metadata_var) if metadata_var else {}
            logger.debug(f"  ✓ Metadata from properties. Keys: {list(metadata.keys())}")
            
            # Log all metadata
            if metadata:
                logger.debug(f"  === Full Metadata Debug ===")
                for key, value in metadata.items():
                    logger.debug(f"    {key}: {value}")
                logger.debug(f"  === End Metadata Debug ===")
            
            # Extract metadata with detailed logging and Variant unwrapping
            artist = metadata.get('xesam:artist', ['Unknown'])
            artist = self._unwrap_variant(artist)
            artist_str = artist[0] if isinstance(artist, list) and artist else "Unknown"
            logger.info(f"  Artist: {artist_str}")
            
            title = metadata.get('xesam:title', 'Unknown')
            title = self._unwrap_variant(title)
            logger.info(f"  Title: {title}")
            
            album = metadata.get('xesam:album', 'Unknown')
            album = self._unwrap_variant(album)
            logger.info(f"  Album: {album}")
            
            duration_us = metadata.get('mpris:length', 0)
            duration_us = self._unwrap_variant(duration_us)
            duration_sec = int(duration_us / 1_000_000) if duration_us else 0
            logger.info(f"  Duration: {duration_sec}s ({self._format_time(duration_sec)})")
            
            # Get Position from properties
            logger.debug(f"  Getting playback position...")
            position_var = properties.get('Position')
            position_us = self._unwrap_variant(position_var) if position_var else 0
            position_sec = int(position_us / 1_000_000) if position_us else 0
            logger.info(f"  Position: {position_sec}s ({self._format_time(position_sec)}) / {duration_sec}s")

            # Log additional metadata if available
            url = metadata.get('xesam:url', 'N/A')
            url = self._unwrap_variant(url)
            logger.debug(f"  URL: {url}")
            
            art_url = metadata.get('mpris:artUrl', 'N/A')
            art_url = self._unwrap_variant(art_url)
            logger.debug(f"  Art URL: {art_url}")
            
            genre = metadata.get('xesam:genre', [])
            genre = self._unwrap_variant(genre)
            if genre:
                genre_str = genre[0] if isinstance(genre, list) else genre
                logger.debug(f"  Genre: {genre_str}")
            
            track_id = metadata.get('mpris:trackid', 'N/A')
            track_id = self._unwrap_variant(track_id)
            logger.debug(f"  Track ID: {track_id}")
            
            # Create and return TrackData
            track_data = TrackData(
                artist=artist_str,
                title=title,
                album=album,
                duration=duration_sec,
                position=position_sec,
                player=player_display_name
            )
            
            logger.info("=" * 70)
            logger.info(f"✓ FOUND PLAYING TRACK - Player: {player_display_name}")
            logger.info("=" * 70)
            
            return track_data
            
        except Exception as e:
            logger.debug(f"  Properties approach failed: {e}", exc_info=True)
            return TrackData.empty()

    async def _list_mpris_players(self, bus):
        """Helper to find all MPRIS-compliant apps currently running."""
        logger.debug("Attempting to list MPRIS players...")
        try:
            # Get introspection first
            logger.debug("Getting DBus introspection...")
            introspection = await bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
            logger.debug("✓ Got introspection data")
            
            # Get proxy object for the DBus service itself with introspection data
            logger.debug("Getting DBus proxy object...")
            dbus_proxy = bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus', introspection)
            logger.debug("✓ Got DBus proxy object")
            
            # Get the standard DBus interface
            logger.debug("Getting DBus interface...")
            dbus_interface = dbus_proxy.get_interface('org.freedesktop.DBus')
            logger.debug("✓ Got DBus interface")
            
            # Call ListNames method
            logger.debug("Calling ListNames() method...")
            all_names = await dbus_interface.call_list_names()
            logger.debug(f"✓ ListNames() returned successfully")
            
            logger.debug(f"Total services on DBus: {len(all_names)}")
            
            # Filter for MPRIS players
            mpris_players = [n for n in all_names if n.startswith('org.mpris.MediaPlayer2')]
            logger.debug(f"MPRIS players found: {len(mpris_players)}")
            
            for player in mpris_players:
                logger.debug(f"  → {player}")
            
            return mpris_players
            
        except Exception as e:
            logger.error(f"✗ Failed to list MPRIS players: {e}", exc_info=True)
            return []

    @staticmethod
    def _format_time(seconds):
        """Convert seconds to MM:SS format"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def _unwrap_variant(value):
        """Unwrap DBus Variant objects to get actual values"""
        from dbus_next.signature import Variant
        if isinstance(value, Variant):
            return value.value
        elif isinstance(value, list) and value and isinstance(value[0], Variant):
            return [v.value if isinstance(v, Variant) else v for v in value]
        return value


async def main():
    logger.info("\n" + "=" * 70)
    logger.info("LYRICTICKER - MPRIS MEDIA PLAYER TEST")
    logger.info("=" * 70)
    logger.info("This script tests all functions in MPRISService class")
    logger.info("It will detect: Spotify, VLC, YouTube Music, MPD, and other MPRIS players")
    logger.info("=" * 70 + "\n")
    
    service = MPRISService()

    try:
        poll_count = 0
        while True:
            poll_count += 1
            logger.debug(f"\n[POLL #{poll_count}] Checking for media playback...")
            
            track = await service.get_current_track()

            if track.player != "None":
                # Clear line and print current status
                progress_bar = _create_progress_bar(track.position, track.duration)
                print(f"\r[{track.player}] {track.artist} - {track.title} {progress_bar}    ", 
                      end="", flush=True)
            else:
                print("\rNo active player found (Status: Playing)...    ", end="", flush=True)

            logger.debug(f"Poll #{poll_count} completed. Waiting 2 seconds before next check...\n")
            await asyncio.sleep(2)  # Poll every 2 seconds for better log readability

    except KeyboardInterrupt:
        logger.info("\n\n" + "=" * 70)
        logger.info("Testing stopped by user (Ctrl+C)")
        logger.info("=" * 70)


def _create_progress_bar(position, duration, bar_length=20):
    """Create a simple progress bar"""
    if duration == 0:
        return "00:00/00:00"
    
    filled = int((position / duration) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    pos_str = f"{position // 60:02d}:{position % 60:02d}"
    dur_str = f"{duration // 60:02d}:{duration % 60:02d}"
    return f"[{bar}] {pos_str}/{dur_str}"


if __name__ == "__main__":
    # Standard entry point for async Python apps
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass