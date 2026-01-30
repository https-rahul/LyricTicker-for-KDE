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
from app.models import TrackData
from app.testing.testPlayer import MPRISService

async def main():
    logger.info("\n" + "=" * 70)
    logger.info("LYRICTICKER - SINGLE TEST (One check only)")
    logger.info("=" * 70 + "\n")
    
    service = MPRISService()
    
    logger.info("Getting current track...")
    track = await service.get_current_track()
    
    if track.player != "None":
        logger.info(f"\n✓ FINAL RESULT:")
        logger.info(f"  Player: {track.player}")
        logger.info(f"  Artist: {track.artist}")
        logger.info(f"  Title: {track.title}")
        logger.info(f"  Album: {track.album}")
        logger.info(f"  Duration: {track.duration}s")
        logger.info(f"  Position: {track.position}s")
    else:
        logger.warning("No playing track found")

if __name__ == "__main__":
    asyncio.run(main())
