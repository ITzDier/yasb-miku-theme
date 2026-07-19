from __future__ import annotations

import asyncio
import html
import json
import sys
import time
from pathlib import Path

try:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    )
    MEDIA_IMPORT_ERROR = None
except (ImportError, OSError) as exc:
    MediaManager = None
    MEDIA_IMPORT_ERROR = str(exc)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MAX_WIDTH = 45
SCROLL_SPEED = 2
SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_FILE = SCRIPT_DIR / "media_cache.json"
READY_ICON = "\U000F0386"
PLAYING_ICON = "\U000F0F70"
PAUSED_ICON = "\U000F040A"


def render_status(icon: str, text: str, text_color: str = "#39c5bb") -> str:
    safe_text = html.escape(text, quote=False)
    return (
        f"<font color='#cba6f7'>{icon}</font>  "
        f"<font color='{text_color}'>{safe_text}</font>"
    )


async def control_media(command: str) -> None:
    if MediaManager is None:
        return
    try:
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()
        if current_session is None:
            return
        if command == "playpause":
            await current_session.try_toggle_play_pause_async()
        elif command == "next":
            await current_session.try_skip_next_async()
        elif command == "prev":
            await current_session.try_skip_previous_async()
    except Exception as exc:
        print(f"Media control failed: {exc}", file=sys.stderr)


async def get_media_info() -> tuple[str, str]:
    if MediaManager is None:
        return "", ""
    try:
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()
        if current_session is None:
            return "", ""

        info = await current_session.try_get_media_properties_async()
        title = (info.title or "").strip()
        artist = (info.artist or "").strip()
        playback_status = current_session.get_playback_info().playback_status
        icon = PLAYING_ICON if playback_status == 4 else PAUSED_ICON
        text = f"{title} - {artist}" if artist else title
        return text, icon
    except Exception as exc:
        print(f"Media query failed: {exc}", file=sys.stderr)
        return "", ""


def get_marquee_text(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    padded_text = text + "   *** "
    offset = int(time.time() * SCROLL_SPEED) % len(padded_text)
    return (padded_text + padded_text)[offset : offset + width]


def load_cache() -> tuple[str, str]:
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return str(data.get("text", "")), str(data.get("icon", ""))
    except (OSError, ValueError, TypeError):
        return "", ""


def save_cache(text: str, icon: str) -> None:
    try:
        CACHE_FILE.write_text(
            json.dumps({"text": text, "icon": icon}, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"Media cache write failed: {exc}", file=sys.stderr)


async def main() -> int:
    command = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if command:
        await control_media(command)
        await asyncio.sleep(0.3)

    if MediaManager is None:
        print(render_status(READY_ICON, "Miku Media: instala requirements.txt", "#f9e2af"))
        if MEDIA_IMPORT_ERROR:
            print(f"winsdk import failed: {MEDIA_IMPORT_ERROR}", file=sys.stderr)
        return 1

    cache_age = time.time() - CACHE_FILE.stat().st_mtime if CACHE_FILE.exists() else 999
    if cache_age > 4 or command:
        text, icon = await get_media_info()
        save_cache(text, icon)
    else:
        text, icon = load_cache()

    if text:
        print(render_status(icon, get_marquee_text(text, MAX_WIDTH)))
    else:
        print(render_status(READY_ICON, "Miku System Ready"))
    return 0


if __name__ == "__main__":
    policy = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if policy is not None:
        asyncio.set_event_loop_policy(policy())
    raise SystemExit(asyncio.run(main()))
