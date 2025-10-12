import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from app.lyrics_provider import LyricsProvider

app = QApplication(sys.argv)
engine = QQmlApplicationEngine()

provider = LyricsProvider()
engine.rootContext().setContextProperty("lyricsProvider", provider)

engine.load("Main.qml")
if not engine.rootObjects():
    sys.exit(-1)
sys.exit(app.exec())
