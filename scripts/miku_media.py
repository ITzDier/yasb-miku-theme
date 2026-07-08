import asyncio
import time
import sys
import os
import json
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

sys.stdout.reconfigure(encoding='utf-8')

MAX_WIDTH = 45 
SCROLL_SPEED = 2 

# Genera el archivo de caché en la misma carpeta que el script de forma segura
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SCRIPT_DIR, "media_cache.json")

async def control_media(command):
    try:
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()
        if current_session:
            if command == "playpause":
                await current_session.try_toggle_play_pause_async()
            elif command == "next":
                await current_session.try_skip_next_async()
            elif command == "prev":
                await current_session.try_skip_previous_async()
    except:
        pass

async def get_media_info():
    try:
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()
        if current_session:
            info = await current_session.try_get_media_properties_async()
            title = info.title
            artist = info.artist
            
            playback_status = current_session.get_playback_info().playback_status
            icon = "󰽰" if playback_status == 4 else "󰐊" 
            
            full_text = f"{title} - {artist}" if artist else title
            return full_text, icon
    except:
        pass
    return "", ""

def get_marquee_text(text, width):
    if len(text) <= width:
        return text
    padded_text = text + "   *** " 
    offset = int(time.time() * SCROLL_SPEED) % len(padded_text)
    return (padded_text + padded_text)[offset:offset+width]

async def main():
    # 1. EJECUCIÓN DE CLICS (Usando la API nativa de Windows que no falla)
    if len(sys.argv) > 1:
        await control_media(sys.argv[1])
        time.sleep(0.3)
        
    # 2. LÓGICA DE CACHÉ (El fix para el bug de YouTube y las flechas)
    age = time.time() - os.path.getmtime(CACHE_FILE) if os.path.exists(CACHE_FILE) else 999
    
    # Solo llamamos a la API de Windows cada 4 segundos, o si hicimos un clic directo
    if age > 4 or len(sys.argv) > 1:
        text, icon = await get_media_info()
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"text": text, "icon": icon}, f)
        except:
            pass
    else:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                text = data.get("text", "")
                icon = data.get("icon", "")
        except:
            text, icon = "", ""

    # 3. DIBUJO DE LA BARRA
    if text:
        display_text = get_marquee_text(text, MAX_WIDTH)
        print(f"<font color='#cba6f7'>{icon}</font>  <font color='#39c5bb'>{display_text}</font>")
    else:
        print(f"<font color='#cba6f7'>󰎆</font>  <font color='#39c5bb'>Miku System Ready</font>")

if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())