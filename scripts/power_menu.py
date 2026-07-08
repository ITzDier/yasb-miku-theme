import sys
import os
import getpass
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QFont, QColor, QPixmap, QPen, QPainter, QPainterPath, QFontMetrics
from miku_avatar_gen import generar_avatar

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DISPLAY_NAME = os.getenv("MIKU_DISPLAY_NAME", getpass.getuser()).strip()
DISPLAY_EMAIL = os.getenv("MIKU_EMAIL", "").strip()
USER_ROLE = os.getenv("MIKU_USER_ROLE", "User").strip()

class OutlinedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setContentsMargins(20, 20, 20, 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = self.font()
        font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(font)

        # Construir el path del texto centrado
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text())
        text_height = fm.ascent()

        x = (self.width() - text_width) / 2
        y = (self.height() / 2) + (text_height / 2) - fm.descent()

        path = QPainterPath()
        path.addText(x, y, font, self.text())

        # Capa 1: Contorno CIAN exterior (más grueso)
        pen_cyan = QPen(QColor("#00F5D4"), 14, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.strokePath(path, pen_cyan)

        # Capa 2: Contorno BLANCO intermedio
        pen_white = QPen(QColor("#FFFFFF"), 7, Qt.PenStyle.SolidLine,
                         Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.strokePath(path, pen_white)

        # Capa 3: Relleno ROSA interior
        painter.fillPath(path, QColor("#FF007F"))

class MikuCosmicPowerMenu(QWidget):
    def __init__(self):
        super().__init__()
        generar_avatar()
        self.init_ui()
        
    def init_ui(self):
        # Volvemos al tamaño fijo centrado que Windows sí acepta sin romper el botón
        self.setFixedSize(900, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        stylesheet = """
            QWidget#MainContainer {
                background-image: url('__SPACE_IMAGE__');
                background-position: center;
                border: 2px solid #7B2CBF;
                border-radius: 24px;
            }
            QLabel#UserMeta {
                color: #00F5D4; /* Azul solicitado */
                font-family: 'Consolas', 'JetBrains Mono', monospace;
                font-size: 14px;
                qproperty-alignment: AlignCenter;
            }
            QWidget#OllamaBox {
                background-color: rgba(22, 26, 29, 0.6);
                border: 1px solid #FFD166;
                border-radius: 12px;
            }
            QLabel#OllamaText {
                color: #00F5D4;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }
            QLabel#OllamaStatus {
                color: #FFD166;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton {
                background-color: rgba(22, 26, 29, 0.8);
                border: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F5D4, stop:1 #7B2CBF);
                border-radius: 14px;
                color: #E0E1DD;
                font-family: 'Segoe UI', sans-serif;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
            }
            QPushButton:hover {
                color: #FFD166;
                background-color: rgba(31, 36, 33, 0.9);
                border-color: #00F5D4;
            }
            QPushButton#BtnCancel {
                border: 2px solid #FFD166;
                color: #FFD166;
            }
            QPushButton#BtnCancel:hover {
                background-color: rgba(255, 209, 102, 0.1);
                color: #FFFFFF;
            }
        """
        self.setStyleSheet(stylesheet.replace("__SPACE_IMAGE__", (ASSETS_DIR / "Space.png").as_posix()))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setObjectName("MainContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 30, 40, 40)
        
        top_row = QHBoxLayout()
        top_row.addStretch()
        
        # --- SECCIÓN OLLAMA ---
        ollama_box = QWidget()
        ollama_box.setObjectName("OllamaBox")
        ollama_box.setFixedSize(220, 80)
        
        # Layout horizontal para poner logo (izquierda) y texto (derecha)
        ollama_layout = QHBoxLayout(ollama_box)
        ollama_layout.setContentsMargins(10, 5, 10, 5)

        # 1. Logo
        llama_label = QLabel()
        llama_path = ASSETS_DIR / "Llama.png"
        if llama_path.exists():
            pixmap = QPixmap(str(llama_path)).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            llama_label.setPixmap(pixmap)
        
        # 2. Layout vertical para los dos textos
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ollama_title = QLabel("Ollama Local AI")
        ollama_title.setObjectName("OllamaText")
        
        ollama_status = QLabel("Status: Ready 󱚥")
        ollama_status.setObjectName("OllamaStatus")
        
        text_layout.addWidget(ollama_title)
        text_layout.addWidget(ollama_status)
        
        # Añadir al layout principal del box
        ollama_layout.addWidget(llama_label)
        ollama_layout.addLayout(text_layout)
        
        top_row.addWidget(ollama_box)
        container_layout.addLayout(top_row)
        
        # --- SECCIÓN DE LA IMAGEN DE PERFIL ---
        avatar_label = QLabel()
        avatar_path = ASSETS_DIR / "miku_avatar.png"
        if avatar_path.exists():
            pixmap = QPixmap(str(avatar_path)).scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            avatar_label.setPixmap(pixmap)
        else:
            # Si no encuentra el archivo local, intenta buscar el icono genérico
            avatar_label.setText("󰣇")
            avatar_label.setStyleSheet("color: #00F5D4; font-size: 70px;")
            
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(avatar_label)
        
        name_label = OutlinedLabel(DISPLAY_NAME.upper())
        name_label.setObjectName("UserName")
        name_label.setMinimumHeight(80)

        font = QFont("Arial Black", 38)
        font.setWeight(QFont.Weight.Black)
        name_label.setFont(font)
        
        user_meta = "  |  ".join(value for value in (USER_ROLE, DISPLAY_EMAIL) if value)
        meta_label = QLabel(user_meta)
        meta_label.setObjectName("UserMeta")
        
        container_layout.addWidget(name_label)
        container_layout.addWidget(meta_label)
        container_layout.addSpacing(30)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        btn_restart = QPushButton("󰜉 Restart")
        btn_sleep = QPushButton("󰤄 Sleep")
        btn_shutdown = QPushButton("󰐥 Shut Down")
        btn_lock = QPushButton("󰌾 Lock")
        btn_signout = QPushButton("󰈆 Sign Out")
        btn_cancel = QPushButton("󰜺 Cancel")
        btn_cancel.setObjectName("BtnCancel")
        
        btn_restart.clicked.connect(lambda: os.system("shutdown /r /t 2"))
        btn_sleep.clicked.connect(lambda: os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"))
        btn_shutdown.clicked.connect(lambda: os.system("shutdown /s /hybrid /t 0"))
        btn_lock.clicked.connect(lambda: os.system("rundll32.exe user32.dll,LockWorkStation"))
        btn_signout.clicked.connect(lambda: os.system("shutdown /l"))
        btn_cancel.clicked.connect(self.close)
        
        grid_layout.addWidget(btn_restart, 0, 0)
        grid_layout.addWidget(btn_sleep, 0, 1)
        grid_layout.addWidget(btn_shutdown, 0, 2)
        grid_layout.addWidget(btn_lock, 1, 0)
        grid_layout.addWidget(btn_signout, 1, 1)
        grid_layout.addWidget(btn_cancel, 1, 2)
        
        container_layout.addLayout(grid_layout)
        
        main_layout.addWidget(container)
        self.setLayout(main_layout)
        self.setWindowOpacity(0.9)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MikuCosmicPowerMenu()
    menu.show()
    sys.exit(app.exec())
