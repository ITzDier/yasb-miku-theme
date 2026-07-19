import sys
import os
import requests
import datetime
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QEvent, QSize
from PyQt6.QtGui import QCursor, QMovie, QColor

# Configura estas variables en Windows antes de iniciar YASB.
API_KEY = os.getenv(
    "YASB_WEATHER_API_KEY", os.getenv("WEATHERAPI_KEY", "")
).strip()
LOCATION = os.getenv(
    "YASB_WEATHER_LOCATION", os.getenv("WEATHER_LOCATION", "YOUR_CITY")
).strip()
API_URL = "https://api.weatherapi.com/v1/forecast.json"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

class MikuWeatherPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_weather_data()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(360, 280)

        # Contenedor Principal
        main_frame = QFrame(self)
        main_frame.setObjectName("MainFrame")
        main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 rgba(20, 20, 35, 0.9), 
                            stop:1 rgba(5, 5, 10, 0.98));
                border: 1px solid #39c5bb;
                border-radius: 14px;
            }
            QLabel {
                color: #cdd6f4;
                font-family: 'JetBrainsMono NFP', 'Bahnschrift', sans-serif;
            }
        """)

        # Glow solo en el frame principal
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(57, 197, 187, 80))
        glow.setOffset(0, 0)
        main_frame.setGraphicsEffect(glow)

        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(20, 20, 20, 20)

        # Ciudad
        self.lbl_city = QLabel(LOCATION.upper(), self)
        self.lbl_city.setStyleSheet("color: #39c5bb; font-size: 16px; font-weight: bold; letter-spacing: 2px;")
        self.lbl_city.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_city)
        
        temp_layout = QHBoxLayout()
        temp_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_gif = QLabel(self)
        self.lbl_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_gif.setFixedSize(90, 90)
        self.movie = QMovie()
        self.lbl_gif.setMovie(self.movie)
        
        self.lbl_temp = QLabel("--°C", self)
        self.lbl_temp.setStyleSheet("color: #cba6f7; font-size: 44px; font-weight: 900;")
        
        self.lbl_cond = QLabel("Cargando...", self)
        self.lbl_cond.setStyleSheet("color: #bac2de; font-size: 13px;")
        self.lbl_cond.setWordWrap(True)
        
        temp_layout.addWidget(self.lbl_gif)
        temp_layout.addWidget(self.lbl_temp)
        temp_layout.addWidget(self.lbl_cond)
        layout.addLayout(temp_layout)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(57, 197, 187, 0.2); max-height: 1px;")
        layout.addWidget(line)

        lbl_forecast_title = QLabel("PRONÓSTICO SIFÓNICO", self)
        lbl_forecast_title.setStyleSheet("color: rgba(57, 197, 187, 0.6); font-size: 11px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(lbl_forecast_title)

        self.forecast_layout = QHBoxLayout()
        layout.addLayout(self.forecast_layout)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main_frame)
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        self.position_popup()

    def position_popup(self):
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() - 40, cursor_pos.y() + 15)

    def showEvent(self, event):
        self.activateWindow() 
        self.setFocus()
        super().showEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.close()

    def get_gif_for_condition(self, condition_text, is_day=1):
        cond_lower = condition_text.lower()
        if "lluvia" in cond_lower or "llovizna" in cond_lower or "aguacero" in cond_lower:
            if is_day == 0:
                return str(ASSETS_DIR / "lluvia_noche.gif")
            else:
                return str(ASSETS_DIR / "lluvia_dia.gif")
        elif "despejado" in cond_lower or "sol" in cond_lower:
            if is_day == 0:
                return str(ASSETS_DIR / "noche.gif")
            else:
                return str(ASSETS_DIR / "sol.gif")
        elif is_day == 0:
            return str(ASSETS_DIR / "noche.gif")
        else:
            return str(ASSETS_DIR / "nubes.gif")

    def load_weather_data(self):
        if not API_KEY or LOCATION == "YOUR_CITY":
            self.lbl_cond.setText("Configura YASB_WEATHER_API_KEY\ny YASB_WEATHER_LOCATION.")
            return

        try:
            response = requests.get(
                API_URL,
                params={"key": API_KEY, "q": LOCATION, "days": 5, "lang": "es"},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                
                current = data["current"]
                temp = int(current["temp_c"])
                condition = current["condition"]["text"]
                humidity = current["humidity"]
                is_day = current["is_day"]
                
                self.lbl_temp.setText(f"{temp}°C")
                self.lbl_cond.setText(f"{condition.upper()}\nHUMEDAD: {humidity}%")

                ruta_gif = self.get_gif_for_condition(condition, is_day)
                self.movie.setFileName(ruta_gif)
                self.movie.setScaledSize(QSize(90, 90))
                self.movie.start()

                # Limpiar pronóstico anterior
                while self.forecast_layout.count():
                    child = self.forecast_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                dias_semana = {"Monday": "LUN", "Tuesday": "MAR", "Wednesday": "MIÉ", "Thursday": "JUE", 
                               "Friday": "VIE", "Saturday": "SÁB", "Sunday": "DOM"}

                forecast_days = data["forecast"]["forecastday"][1:5]

                for day in forecast_days:
                    date_obj = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
                    day_name = dias_semana.get(date_obj.strftime("%A"), date_obj.strftime("%a").upper())
                    max_t = int(day["day"]["maxtemp_c"])
                    min_t = int(day["day"]["mintemp_c"])
                    day_condition = day["day"]["condition"]["text"]

                    container_widget = QFrame()
                    container_widget.setStyleSheet("""
                        QFrame {
                            border: 1px solid #39c5bb;
                            border-radius: 8px;
                            background: rgba(20, 20, 35, 0.6);
                            padding: 4px;
                        }
                        QFrame:hover {
                            border-color: #cba6f7;
                            background: rgba(57, 197, 187, 0.08);
                        }                           
                    """)

                    day_box = QVBoxLayout(container_widget)
                    day_box.setContentsMargins(6, 4, 6, 4)
                    day_box.setSpacing(2)

                    lbl_day = QLabel(day_name)
                    lbl_day.setStyleSheet("color: #39c5bb; font-size: 11px; font-weight: bold; border: none; background: transparent;")
                    lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    lbl_day_gif = QLabel()
                    lbl_day_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_day_gif.setFixedSize(48, 48)
                    lbl_day_gif.setStyleSheet("border: none; background: transparent;")
                    day_movie = QMovie(self.get_gif_for_condition(day_condition))
                    day_movie.setScaledSize(QSize(48, 48))
                    lbl_day_gif.setMovie(day_movie)
                    day_movie.start()
                    lbl_day_gif.setProperty("movie_ref", day_movie)

                    lbl_temps = QLabel(f"{max_t}°/{min_t}°")
                    lbl_temps.setStyleSheet("color: #cdd6f4; font-size: 11px; font-weight: 600; border: none; background: transparent;")
                    lbl_temps.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    day_box.addWidget(lbl_day)
                    day_box.addWidget(lbl_day_gif)
                    day_box.addWidget(lbl_temps)

                    self.forecast_layout.addWidget(container_widget)

            else:
                self.lbl_cond.setText("Error de red.")
        except Exception as e:
            self.lbl_cond.setText(f"Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    popup = MikuWeatherPopup()
    popup.show()
    sys.exit(app.exec())
