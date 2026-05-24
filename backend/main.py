import logging
import sys
import asyncio
from pathlib import Path
import signal

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from dbus_next.aio import MessageBus
from qasync import QEventLoop
from aiohttp import web

from backend.mpris_service import MPRISService
from backend.lyrics_provider import LyricsProvider
from backend.lyrics.manager import LyricsManager

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("LyricTicker")

async def main():
    logger.info("Starting LyricTicker Engine...")
    try:
        bus = await MessageBus().connect()
        logger.info("Connected to D-Bus Session Bus")

        mpris_service = MPRISService(bus)
        lyrics_manager = LyricsManager()
        logger.info("MPRISService initialised")

        provider = LyricsProvider(mpris_service, lyrics_manager)  # ← updated

        server_app = web.Application()
        server_app['lyrics_provider'] = provider
        server_app.router.add_get('/', handle_plasmoid_request)

        runner = web.AppRunner(server_app)
        await runner.setup()
        try:
            site = web.TCPSite(runner, '127.0.0.1', 5000)
            await site.start()
            logger.info("Integrated server listening on port 5000")

            engine = QQmlApplicationEngine()
            provider.timer.start(200)
            engine.rootContext().setContextProperty("lyricsProvider", provider)
            logger.info("✓ QML Context Properties set")

            qml_path = str(ROOT_DIR / "dev" / "AppWindow.qml")
            engine.load(qml_path)
            if not engine.rootObjects():
                logger.error("✗ QML failed to load. Check AppWindow.qml syntax.")
                return

            stop_event = asyncio.Future()

            def on_quit():
                if not stop_event.done():
                    stop_event.set_result(True)

            QGuiApplication.instance().aboutToQuit.connect(on_quit)
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGTERM, on_quit)
            loop.add_signal_handler(signal.SIGINT, on_quit)

            await stop_event

            provider.clear()
            await asyncio.sleep(0.5)

        finally:
            await runner.cleanup()

    except Exception as e:
        logger.error(f"CRITICAL FAILURE during startup: {e}", exc_info=True)
        return

async def handle_plasmoid_request(request):
    provider = request.app['lyrics_provider']
    return web.Response(
        text=provider.current_lyric,
        headers={
            'Access-Control-Allow-Origin': '*',
            "Content-Type": "text/plain"
        }
    )

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Shutting down via User Interrupt...")
    except Exception as e:
        logger.error(f"Unhandled Exception: {e}")
    finally:
        if not loop.is_closed():
            loop.close()