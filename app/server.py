# server.py
from flask import Flask, Response
import threading
import os

CACHE_FILE = os.path.expanduser("~/.cache/lyricticker/current.txt")
app = Flask(__name__)

@app.route("/")
def current_lyric():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            text = f.read()
        return Response(text, mimetype="text/plain")
    except:
        return Response("Waiting for lyrics…", mimetype="text/plain")

def run_server():
    print("Starting Lyric server on http://127.0.0.1:5000")
    # Use host=127.0.0.1 and disable reloader for threading
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def start_server():
    # Non-daemon thread
    t = threading.Thread(target=run_server)
    t.start()
    return t

# ✅ Only run server automatically when this file is run directly
if __name__ == "__main__":
    start_server()
