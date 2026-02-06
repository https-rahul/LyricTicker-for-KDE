import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from app.lyrics_provider import LyricsProvider
from app import server  # Import the module

# Start Flask server
server.start_server()  # ✅ Explicitly start server thread

app = QApplication(sys.argv)
engine = QQmlApplicationEngine()

provider = LyricsProvider()
engine.rootContext().setContextProperty("lyricsProvider", provider)

basedir = os.path.dirname(__file__)
qml_path = os.path.join(basedir, 'AppWindow.qml')

engine.load(QUrl.fromLocalFile(qml_path))

if not engine.rootObjects():
    sys.exit(-1)
sys.exit(app.exec())
