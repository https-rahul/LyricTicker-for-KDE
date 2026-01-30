import logging
from dbus_next import Message, MessageType
from dbus_next.signature import Variant

logger = logging.getLogger(__name__)


def unwrap_variant(value):
    """
    Recursively unwraps DBus Variant objects.
    Industry Standard: DBus returns data wrapped in signatures (e.g., <v 'Title'>).
    This function peels those layers back to get raw Python types.
    """
    if isinstance(value, Variant):
        return unwrap_variant(value.value)
    if isinstance(value, list):
        return [unwrap_variant(v) for v in value]
    if isinstance(value, dict):
        return {k: unwrap_variant(v) for k, v in value.items()}
    return value


async def list_mpris_players(bus):
    """
    Queries the DBus daemon for all currently registered services
    and filters for those implementing the MPRIS spec.
    """
    try:
        reply = await bus.call(
            Message(
                destination='org.freedesktop.DBus',
                path='/org/freedesktop/DBus',
                interface='org.freedesktop.DBus',
                member='ListNames'
            )
        )

        if reply.message_type == MessageType.METHOD_RETURN:
            players = [n for n in reply.body[0] if n.startswith('org.mpris.MediaPlayer2')]
            logger.debug(f"Found MPRIS players: {players}")
            return players
    except Exception as e:
        logger.error(f"Failed to list MPRIS players: {e}")

    return []


def format_time(seconds: int) -> str:
    """Helper to convert raw seconds into human-readable MM:SS."""
    if not seconds or seconds < 0:
        return "00:00"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def create_progress_bar(position: int, duration: int, length: int = 20) -> str:
    """Generates a visual text-based progress bar."""
    if duration <= 0:
        return "░" * length

    fraction = min(position / duration, 1.0)
    filled = int(length * fraction)
    return "█" * filled + "░" * (length - filled)