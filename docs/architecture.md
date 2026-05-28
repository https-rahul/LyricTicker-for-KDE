# LyricTicker — Architecture Documentation

## Overview

LyricTicker consists of two independent components that communicate over a local HTTP server:

1. **Python Backend** — detects the currently playing track, fetches synced lyrics, and serves the current lyric line over HTTP
2. **KDE Plasma Plasmoid** — a QML widget that polls the HTTP server and displays the current lyric line in the panel

These two components run in separate processes by design — the Plasma shell cannot share memory with external Python processes, so HTTP is used as the communication bridge.

---

## High Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Backend Process                   │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │ MPRISService│───▶│LyricsProvider│◀───│ LyricsManager │   │
│  │  (D-Bus)    │    │  (Qt Bridge) │    │  (Fetcher)    │   │
│  └─────────────┘    └──────┬───────┘    └───────────────┘   │
│         ▲                  │                    │           │
│         │                  │                    ▼           │
│    D-Bus Session       aiohttp            ┌──────────┐      │
│    Bus (MPRIS2)        Server             │  LRCLib  │      │
│                            │              │ NetEase  │      │
│                            │              │ QQ Music │      │
│                            ▼              │  Kugou   │      │
│                     127.0.0.1:5000        └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                             │
                    HTTP GET every 200ms
                             │
┌────────────────────────────▼────────────────────────────────┐
│                   Plasma Shell Process                      │
│                                                             │
│              ┌─────────────────────────┐                    │
│              │   Plasmoid (main.qml)   │                    │
│              │   XHR poll → port 5000  │                    │
│              │   displays lyric line   │                    │
│              └─────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. MPRISService (`backend/mpris_service.py`)

Responsible for detecting the currently playing track via the MPRIS2 D-Bus interface.

**How it works:**
- Connects to the D-Bus session bus on startup
- Scans all D-Bus services for names starting with `org.mpris.MediaPlayer2`
- Queries each player's `PlaybackStatus` — returns the first one with status `"Playing"`
- Returns a `TrackData` object with artist, title, album, duration, and current position

**Key design decisions:**
- Uses `dbus-next` async library — non-blocking, compatible with the `qasync` event loop
- Sends raw `Message` objects instead of using the introspection API — more compatible with edge cases like Brave browser and Spotify
- Player display names are resolved via a lookup dict (`PLAYER_NAMES`) to handle D-Bus instance suffixes (e.g. `brave.instance2` → `"Brave"`)

**D-Bus message flow:**
```
MPRISService.get_current_track()
    → DBus.ListNames()                          # get all services
    → filter org.mpris.MediaPlayer2.*           # find media players
    → Properties.GetAll(MediaPlayer2.Player)    # get playback state
    → return TrackData if status == "Playing"
```

---

### 2. LyricsManager (`backend/lyrics/manager.py`)

Responsible for fetching synced lyrics from multiple sources in priority order.

**How it works:**
- Holds an ordered list of `BaseLyricsProvider` implementations
- Tries each source in order, returns the first successful result
- Only accepts synced (LRC-formatted) lyrics — plain text is rejected
- If all sources fail, returns `None`

**Adding a new source:**
1. Create `backend/lyrics/yoursource.py` implementing `BaseLyricsProvider`
2. Add it to `self.sources` list in `manager.py`
3. No other files need changing

**Current source priority:**
```
1. LRCLib      (lrclib.net — open, free, no auth required)
2. NetEase     (planned)
3. QQ Music    (planned)
4. Kugou       (planned)
```

---

### 3. LyricsProvider (`backend/lyrics_provider.py`)

The central coordinator — bridges MPRIS track detection, lyrics fetching, and QML display. Also exposes the current lyric as a Qt property for `AppWindow.qml`.

**How it works:**
- A `QTimer` fires every 200ms (configurable via `TIMER_INTERVAL_MS` in `constants.py`)
- Each tick calls `MPRISService.get_current_track()` asynchronously
- If the track has changed, cancels any in-flight fetch task and starts a new one
- If the track is the same, finds the correct lyric line for the current playback position using binary-search style iteration over timestamps
- Writes the current lyric to a cache file (`~/.cache/lyricticker/current.txt`) only when it changes

**Lyric sync algorithm:**
```python
for i, (timestamp, text) in enumerate(timestamped_lyrics):
    if track.position >= timestamp:
        new_index = i
    else:
        break  # timestamps are sorted, stop early
```

**Race condition protection:**
When the user switches tracks quickly, multiple fetch tasks could run concurrently and write conflicting lyrics state. This is prevented by cancelling the previous fetch task before starting a new one:
```python
if self._fetch_task and not self._fetch_task.done():
    self._fetch_task.cancel()
self._fetch_task = loop.create_task(self.fetch_new_song_lyrics(track))
```

**Two consumers:**
- `AppWindow.qml` (dev only) — reads `lyricsProvider` directly as a Qt context property injected by the engine
- `main.qml` (plasmoid) — polls the HTTP server at `127.0.0.1:5000`

---

### 4. aiohttp HTTP Server (`backend/main.py`)

A minimal single-route HTTP server that exposes the current lyric line to the plasmoid.

**Why HTTP?**
The Plasma shell runs in a separate process from the Python backend. QML running inside the Plasma shell cannot access Python objects directly. HTTP is the simplest bridge between the two processes.

**Route:**
```
GET http://127.0.0.1:5000/
→ 200 text/plain  "current lyric line"
→ 200 text/plain  ""  (no track playing or no lyrics found)
```

**Configuration:**
Host and port are defined in `backend/constants.py`:
```python
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 5000
```
The port in `plasmoid/contents/ui/main.qml` must match `HTTP_PORT`.

**Shutdown:**
On application exit, `LyricsProvider.clear()` is called before the server shuts down. This ensures the plasmoid receives one final empty response and clears its display rather than freezing on the last lyric.

---

### 5. Plasmoid (`plasmoid/contents/ui/main.qml`)

A minimal KDE Plasma widget that displays the current lyric line in the panel.

**How it works:**
- A `QML Timer` fires every 200ms
- Each tick sends an `XMLHttpRequest` to `http://127.0.0.1:5000/`
- If the response differs from the currently displayed text, updates the label
- Includes error counting and backoff — after 10 consecutive failures, polling slows to every 5 seconds to avoid hammering a stopped backend

**Why XHR polling instead of WebSockets?**
QML's networking support in the Plasma shell environment is limited. XHR is the most reliable and widely supported option. The 200ms interval matches the backend's timer, so there is no meaningful latency difference.

---

### 6. AppWindow.qml (`dev/AppWindow.qml`)

A standalone Qt window used during development only. Not installed for end users.

Displays three lyric lines simultaneously:
- Previous line (dimmed)
- Current line (highlighted)
- Next line (dimmed)

Reads directly from the `lyricsProvider` Qt context property — no HTTP involved. Launched only when `LYRICTICKER_DEV=1` environment variable is set.

---

## Event Loop Architecture

LyricTicker fuses two event loops using `qasync`:

```
QEventLoop (Qt)  +  asyncio event loop
         ↓
      qasync.QEventLoop
         ↓
runs both Qt signals/slots AND async coroutines
on the same thread
```

This is necessary because:
- PySide6 requires Qt to run on the main thread
- D-Bus (dbus-next) and aiohttp require asyncio
- Without fusion, the two loops would block each other

---

## Data Flow — Full Example

```
User plays "Bohemian Rhapsody" on Spotify

1. MPRISService detects org.mpris.MediaPlayer2.spotify
2. Queries D-Bus → PlaybackStatus: "Playing"
3. Returns TrackData(player="Spotify", title="Bohemian Rhapsody", artist="Queen", ...)

4. LyricsProvider.sync_logic() detects new track ID
5. Cancels any previous fetch task
6. Creates new task: fetch_new_song_lyrics(track)

7. LyricsManager tries LRCLib first
8. LRCLib fetches https://lrclib.net/api/get?artist_name=Queen&track_name=Bohemian+Rhapsody
9. Returns LRC-formatted synced lyrics string

10. LyricsProvider.parse_synced_lyrics() parses timestamps
11. _timestamped_lyrics = [(0.0, ""), (4.2, "Is this the real life?"), ...]

12. Every 200ms, sync_logic() finds the correct line for track.position
13. _current_lyric = "Is this the real life?"
14. Written to ~/.cache/lyricticker/current.txt

15. Plasmoid XHR polls http://127.0.0.1:5000/
16. Gets "Is this the real life?"
17. lyricLabel.text updates in panel
```

---

## File Structure

```
LyricTicker-for-KDE/
├── backend/
│   ├── lyrics/
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base class for all sources
│   │   ├── manager.py        # Source priority orchestrator
│   │   └── lrclib.py         # LRCLib provider implementation
│   ├── constants.py          # HTTP host/port, cache path, timer intervals
│   ├── models.py             # TrackData dataclass
│   ├── mpris_service.py      # D-Bus/MPRIS2 track detection
│   ├── lyrics_provider.py    # Qt bridge, sync logic, cache writer
│   └── main.py               # Entry point, event loop, HTTP server
├── plasmoid/
│   ├── contents/ui/
│   │   └── main.qml          # Plasma widget UI
│   └── metadata.json         # KDE package metadata
├── dev/
│   └── AppWindow.qml         # Debug window (dev mode only)
├── scripts/
│   ├── install.sh            # Installs plasmoid + systemd service
│   └── uninstall.sh          # Removes all installed components
└── docs/
    ├── architecture.md       # This document
    └── audit.md              # Pre-release code audit
```

---

## Configuration Reference

All configurable values live in `backend/constants.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `HTTP_HOST` | `127.0.0.1` | Interface the HTTP server binds to |
| `HTTP_PORT` | `5000` | Port the HTTP server listens on |
| `CACHE_FILE` | `~/.cache/lyricticker/current.txt` | Current lyric cache path |
| `TIMER_INTERVAL_MS` | `200` | How often to poll MPRIS and sync lyrics (ms) |
| `MPRIS_SCAN_INTERVAL_S` | `5.0` | How often to rescan D-Bus for new players (s) |

**Note:** If you change `HTTP_PORT`, you must also update the URL in `plasmoid/contents/ui/main.qml`.