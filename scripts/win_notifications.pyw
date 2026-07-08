import sqlite3, os, time
from pathlib import Path

temp_file = Path(__file__).resolve().with_name("notif_count.txt")
db_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db")

while True:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Notification WHERE NotifiedTime > 0")
        count = cursor.fetchone()[0]
        conn.close()
        # Si hay notificaciones, escribimos el número, si no, un espacio vacío
        valor = str(count) if count > 0 else ""
        with open(temp_file, "w") as f:
            f.write(valor)
    except:
        with open(temp_file, "w") as f:
            f.write("")
    time.sleep(5)
