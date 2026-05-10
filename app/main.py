import logging
import sys
import asyncio
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from dbus_next.aio import MessageBus
from qasync import QEventLoop
from aiohttp import web

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("LyricTicker")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.mpris_service import MPRISService
from app.lyrics_service import LyricsService
from app.lyrics_provider import LyricsProvider

async def main():
    logger.info("Starting LyricTicker Engine...")

    try:
        #D-Bus
        bus = await MessageBus().connect()
        logger.info("Connected to D-Bus Session Bus")

        # B. Initialize Backend Services
        mpris_service = MPRISService(bus)
        lyrics_service = LyricsService()

        logger.info(mpris_service)

        # C. Initialize the Provider (The Bridge)
        # We define it here so it stays in scope
        provider = LyricsProvider(mpris_service, lyrics_service)

        server_app = web.Application()
        server_app['lyrics_provider'] = provider
        server_app.router.add_get('/', handle_plasmoid_request)

        runner = web.AppRunner(server_app)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', 5000)
        await site.start()
        logger.info("Integrated server listening on port 5000")

        # D. Initialize QML Engine
        engine = QQmlApplicationEngine()

        provider.timer.start(200)

        # E. Inject Provider into QML Context
        # This MUST happen after 'engine' is created but BEFORE 'engine.load'
        engine.rootContext().setContextProperty("lyricsProvider", provider)
        logger.info("✓ QML Context Properties set")

        # F. Load the UI
        qml_path = str(ROOT_DIR / "AppWindow.qml")
        engine.load(qml_path)

        if not engine.rootObjects():
            logger.error("✗ QML failed to load. Check AppWindow.qml syntax.")
            return

        # G. App Lifecycle Management
        # Keep the coroutine alive until the user closes the window
        stop_event = asyncio.Future()
        QGuiApplication.instance().aboutToQuit.connect(lambda: stop_event.set_result(True))

        logger.info("Application is running. Monitoring media...")
        await stop_event

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
    # Initialize the Qt Application
    app = QGuiApplication(sys.argv)

    # Create the fused Event Loop (Qt + Asyncio)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Shutting down via User Interrupt...")
    except Exception as e:
        logger.error(f"Unhandled Exception: {e}")
    finally:
        # Standard cleanup
        if not loop.is_closed():
            loop.close()