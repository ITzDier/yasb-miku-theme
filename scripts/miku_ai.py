import datetime
import html
import json
import os
import sys
import threading

import requests
from PyQt6.QtCore import QEvent, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTextEdit, QToolButton, QVBoxLayout, QWidget,
)

# ── Rutas ─────────────────────────────────────────────────────────────
BASE_DIR          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_FRAME_PATH  = os.path.join(BASE_DIR, "assets", "Frame_Miku_AI_Clean.png")
LEGACY_FRAME_PATH = os.path.join(BASE_DIR, "assets", "Frame.png")
FRAME_IMAGE_PATH  = CLEAN_FRAME_PATH if os.path.exists(CLEAN_FRAME_PATH) else LEGACY_FRAME_PATH
AVATAR_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "Miku_Bot.png")

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
DISPLAY_NAME = os.getenv("MIKU_DISPLAY_NAME", "Usuario").strip() or "Usuario"
DISPLAY_LOCATION = os.getenv("MIKU_LOCATION", "").strip()
CLOCK_LABEL = os.getenv("MIKU_CLOCK_LABEL", "LOCAL").strip() or "LOCAL"

# ── Paleta ────────────────────────────────────────────────────────────
MIKU_CYAN = "#39c5bb"
MIKU_BLUE = "#1e90ff"
TEXT      = "#d7def8"
RED       = "#f38ba8"
GREEN     = "#a6e3a1"
FRAME_OPACITY = 0.96

WIN_W, WIN_H = 960, 678

# Constantes para los botones de ventana (posición absoluta)
CTRL_TOP   = 10
CTRL_RIGHT = 16
CTRL_SIZE  = 38
CTRL_GAP   = 8
TOOLBAR_CENTER_RATIOS = (0.124, 0.309, 0.499, 0.688, 0.874)
TOOLBAR_X_OFFSET = -50


# ─────────────────────────────────────────────────────────────────────
class SpaceFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._px = QPixmap(FRAME_IMAGE_PATH)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = 28
        frame_rect = QRectF(self.rect().adjusted(1, 1, -1, -1))
        frame_path = QPainterPath()
        frame_path.addRoundedRect(frame_rect, radius, radius)
        p.setClipPath(frame_path)

        if not self._px.isNull():
            scaled = self._px.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            p.setOpacity(FRAME_OPACITY)
            p.drawPixmap(0, 0, scaled)
            p.setOpacity(1.0)
        else:
            g = QLinearGradient(0, 0, self.width(), self.height())
            g.setColorAt(0, QColor(8, 10, 25))
            g.setColorAt(1, QColor(0, 42, 58))
            p.fillRect(self.rect(), g)
        p.fillRect(self.rect(), QColor(3, 8, 18, 34))
        p.setClipping(False)
        border_rect = self.rect().adjusted(3, 3, -3, -3)
        p.setPen(QPen(QColor(57, 197, 187, 220), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(border_rect, radius, radius)
        super().paintEvent(event)


# ─────────────────────────────────────────────────────────────────────
def _make_btn(parent, text="", tooltip="", icon_path=None,
              icon_size=34, danger=False):
    """
    Crea un QToolButton hijo DIRECTO de `parent`.
    parent debe ser el widget cuyo layout lo va a contener.
    """
    btn = QToolButton(parent)          # ← parent = el contenedor real
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedSize(82, 42)
    btn.setText(text)
    btn.setIconSize(QSize(icon_size, icon_size))
    if icon_path and os.path.exists(icon_path):
        btn.setIcon(QIcon(icon_path))
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    accent = RED if danger else MIKU_CYAN
    rgb    = "243,139,168" if danger else "57,197,187"
    btn.setStyleSheet(f"""
        QToolButton {{
            background  : rgba(5,12,24,0.20);
            border      : 1px solid rgba({rgb},0.25);
            border-radius: 8px;
            color       : {accent};
            font-family : 'JetBrainsMono NFP','Segoe UI Symbol',sans-serif;
            font-size   : 22px;
            font-weight : 700;
        }}
        QToolButton:hover {{
            background  : rgba({rgb},0.18);
            border-color: rgba({rgb},0.80);
            color: #fff;
        }}
        QToolButton:pressed  {{ background: rgba({rgb},0.32); }}
        QToolButton:disabled {{
            color: rgba(139,149,181,0.40);
            border-color: rgba(139,149,181,0.14);
        }}
    """)
    return btn


# ─────────────────────────────────────────────────────────────────────
class MikuAIPopup(QWidget):
    chunk_received    = pyqtSignal(int, str)
    response_finished = pyqtSignal(int, str, bool, bool)

    def __init__(self):
        super().__init__()
        self._attached_file  = None
        self._drag_pos       = None
        self._generation_id  = 0
        self._is_generating  = False
        self._stop_requested = False
        self._active_resp    = None
        self._messages       = []

        self._build_ui()
        self.chunk_received.connect(self._on_chunk)
        self.response_finished.connect(self._on_response_finished)

        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick)
        self._clock.start(1000)
        self._tick()

        self._add_assistant_message(
            f"{self._greeting()}, {DISPLAY_NAME}. Sistema en línea. "
            "Conectado a modelo local. ¿En qué te ayudo hoy?"
        )

    # ─── UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("MIKU.AI")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(WIN_W, WIN_H)
        self.setMinimumSize(760, 536)

        # Capa 0 – layout raíz del window (transparente)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)

        # Capa 1 – SpaceFrame llena el window
        self.frame = SpaceFrame(self)
        self.frame.setSizePolicy(QSizePolicy.Policy.Expanding,
                                  QSizePolicy.Policy.Expanding)
        glow = QGraphicsDropShadowEffect(self.frame)
        glow.setBlurRadius(34)
        glow.setOffset(0, 0)
        glow.setColor(QColor(57, 197, 187, 135))
        self.frame.setGraphicsEffect(glow)
        root.addWidget(self.frame)

        # Controles de ventana – posición absoluta SOBRE el frame
        self._build_window_controls()

        # Capa 2 – layout de contenido dentro del frame
        # top=56 deja espacio libre a los botones □/×
        inner = QVBoxLayout(self.frame)
        inner.setContentsMargins(50, 35, 60, 35)
        inner.setSpacing(0)

        inner.addLayout(self._make_header())
        inner.addSpacing(65)
        inner.addWidget(self._make_chat(), stretch=1)
        inner.addSpacing(15)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(-50, 28, 0, 0) # El -15 empuja la caja a la izquierda
        inner.addWidget(self._make_input())
        inner.addLayout(input_layout)
        inner.addSpacing(0)
        inner.addWidget(self._make_toolbar())

        self._center()

    # ── controles de ventana (posición absoluta) ─────────────────────
    def _build_window_controls(self):
        _s = """
            QPushButton {{
                background   : rgba(5,12,24,0.15);
                border       : 1px solid rgba({rgb},0.22);
                border-radius: 7px;
                color        : {accent};
                font-family  : 'Segoe UI Symbol',sans-serif;
                font-size    : 22px; font-weight: 800;
            }}
            QPushButton:hover {{
                background  : rgba({rgb},0.22);
                border-color: rgba({rgb},0.80);
                color: #fff;
            }}
            QPushButton:pressed {{ background: rgba({rgb},0.38); }}
        """
        self.btn_max   = QPushButton("□", self.frame)
        self.btn_close = QPushButton("×", self.frame)
        self.btn_max.setStyleSheet(
            _s.format(accent=MIKU_CYAN, rgb="57,197,187"))
        self.btn_close.setStyleSheet(
            _s.format(accent=RED, rgb="243,139,168"))
        for btn in (self.btn_max, self.btn_close):
            btn.setFixedSize(CTRL_SIZE, CTRL_SIZE)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.raise_()
        self.btn_max.clicked.connect(self._toggle_maximized)
        self.btn_close.clicked.connect(QApplication.instance().quit)
        self._reposition_controls()

    def _reposition_controls(self):
        fw = self.frame.width() or (WIN_W - 20)
        xc = fw - CTRL_RIGHT - CTRL_SIZE
        xm = xc - CTRL_SIZE - CTRL_GAP
        self.btn_close.move(xc, CTRL_TOP)
        self.btn_max.move(xm, CTRL_TOP)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_controls()
        self._position_toolbar_buttons()

    # ── header ───────────────────────────────────────────────────────
    def _make_header(self):
        row = QHBoxLayout()
        row.setSpacing(14)
        
        # Aplicamos un margen superior negativo al row completo para forzarlo a subir
        row.setContentsMargins(0, -10, 0, 0) 

        av = QLabel(self.frame)
        av.setFixedSize(100, 82)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(AVATAR_IMAGE_PATH):
            av.setPixmap(QPixmap(AVATAR_IMAGE_PATH).scaled(
                96, 78, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            av.setText("MIKU")
        av.setStyleSheet(
            f"background:transparent;border:0;color:{MIKU_CYAN};"
            f"font-size:20px;font-weight:800;")

        col = QVBoxLayout()
        col.setSpacing(2)
        # Margen superior en 0, el row ya lo está empujando hacia arriba
        col.setContentsMargins(0, 0, 0, 0) 

        lbl = QLabel("MIKU AI CHAT (OLLAMA)", self.frame)
        lbl.setStyleSheet(
            f"color:{MIKU_CYAN};background:transparent;"
            f"font-family:'JetBrainsMono NFP','Bahnschrift',monospace;"
            f"font-size:26px;font-weight:800;letter-spacing:2px;")

        self.lbl_clock = QLabel("", self.frame)
        self.lbl_clock.setMinimumHeight(36)
        self.lbl_clock.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.lbl_clock.setStyleSheet(
            f"background:rgba(5,12,24,0.72);"
            f"border:2px solid rgba(57,197,187,0.48);border-radius:7px;"
            f"color:{TEXT};font-family:'JetBrainsMono NFP',Consolas,monospace;"
            f"font-size:18px;font-weight:700;padding:0 14px;")

        col.addWidget(lbl)
        col.addWidget(self.lbl_clock)
        col.addStretch(1)
        
        row.addWidget(av, alignment=Qt.AlignmentFlag.AlignTop)
        row.addLayout(col, stretch=1)
        return row

    # ── chat ─────────────────────────────────────────────────────────
    def _make_chat(self):
        self.chat = QTextEdit(self.frame)
        self.chat.setReadOnly(True)
        self.chat.setAcceptRichText(True)
        self.chat.setSizePolicy(QSizePolicy.Policy.Expanding,
                                 QSizePolicy.Policy.Expanding)
        self.chat.setStyleSheet(f"""
            QTextEdit {{
                background: transparent; /* Hace que se vea el fondo espacial */
                border: none; /* Quitamos el borde para que no parezca una caja */
                color: {TEXT};
                font-family: 'JetBrainsMono NFP', Consolas, monospace;
                font-size: 15px; 
                padding: 6px 12px; /* Un poco de padding para que no pegue con las orillas */
                selection-background-color: rgba(57, 197, 187, 0.35);
            }}
            QScrollBar:vertical {{
                background: transparent; width: 7px; margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(57,197,187,0.48); border-radius: 3px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self.chat.document().setDocumentMargin(0)
        self.chat.setViewportMargins(0, 0, 0, 0)
        return self.chat

    # ── input ────────────────────────────────────────────────────────
    def _make_input(self):
        self.input_field = QLineEdit(self.frame)
        self.input_field.setPlaceholderText(
            "Escribe tu prompt aquí y presiona Enter…")
        self.input_field.setMinimumHeight(48)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(5,12,24,0.30);
                border: none;
                border-bottom: 1px solid rgba(57,197,187,0.3);
                border-radius: 4px; color: #f4f7ff;
                font-family: 'JetBrainsMono NFP',Consolas,monospace;
                font-size: 18px; 
                padding: 0 5px; /* <-- Reducido para que el texto inicie más a la izquierda */
            }}
            QLineEdit:focus {{
                background: rgba(8,18,35,0.60);
                border-bottom: 1px solid {MIKU_CYAN};
            }}
        """)
        self.input_field.returnPressed.connect(self._send)
        return self.input_field

    # ── toolbar ──────────────────────────────────────────────────────
    def _make_toolbar(self):
        """
        QWidget opaco como contenedor.
        Los botones se crean con parent=bar para que Qt
        no los renderice dos veces.
        """
        bar = QWidget(self.frame)
        self.toolbar_bar = bar
        bar.setFixedHeight(54)
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bar.setStyleSheet("background: transparent;")

        # ↓ parent = bar  (no self.frame)
        self.btn_attach = _make_btn(bar, "\uf0c6", "Adjuntar archivo de texto")
        self.btn_send   = _make_btn(bar, "\uf1d8", "Enviar (Enter)")
        self.btn_stop   = _make_btn(bar, "\uf04d", "Detener generación", danger=True)
        self.btn_clear  = _make_btn(bar, "\uf1f8", "Limpiar chat")
        self.btn_miku   = _make_btn(bar, "",       "Enfocar prompt",
                                    AVATAR_IMAGE_PATH, icon_size=34)

        self.btn_attach.clicked.connect(self._attach_file)
        self.btn_send.clicked.connect(self._send)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_miku.clicked.connect(self._focus_prompt)
        self.btn_stop.setEnabled(False)

        self._toolbar_buttons = (
            self.btn_attach, self.btn_send, self.btn_stop,
            self.btn_clear, self.btn_miku,
        )
        self._position_toolbar_buttons()

        return bar

    def _position_toolbar_buttons(self):
        if not hasattr(self, "toolbar_bar") or not hasattr(self, "_toolbar_buttons"):
            return

        frame_w = self.frame.width() or (WIN_W - 20)
        bar_x = self.toolbar_bar.x()
        y = max(0, (self.toolbar_bar.height() - self.btn_attach.height()) // 2)

        for ratio, btn in zip(TOOLBAR_CENTER_RATIOS, self._toolbar_buttons):
            center_x = round(frame_w * ratio) - bar_x + TOOLBAR_X_OFFSET
            btn.move(center_x - btn.width() // 2, y)
            btn.raise_()

    # ── helpers ──────────────────────────────────────────────────────
    def _greeting(self):
        h = datetime.datetime.now().hour
        if 5  <= h < 12: return "Buenos días"
        if 12 <= h < 19: return "Buenas tardes"
        return "Buenas noches"

    def _tick(self):
        n = datetime.datetime.now()
        self.lbl_clock.setText(f"{CLOCK_LABEL} [{n:%Y-%m-%d}] | [{n:%H:%M:%S}]")

    def _center(self):
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center().x() - self.width()  // 2,
                  geo.center().y() - self.height() // 2)

    def _toggle_maximized(self):
        if self.isMaximized():
            self.showNormal(); self.btn_max.setText("□")
        else:
            self.showMaximized(); self.btn_max.setText("❐")

    def _focus_prompt(self):
        self.input_field.setFocus()
        sb = self.chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── adjuntar ─────────────────────────────────────────────────────
    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo", os.path.expanduser("~"),
            "Texto (*.txt *.py *.md *.json *.csv *.log *.yaml);;Todos (*.*)",
        )
        if not path: return
        self._attached_file = path
        self._add_system_message(
            f"Archivo adjunto listo: {os.path.basename(path)}")
        self.btn_attach.setStyleSheet(
            self.btn_attach.styleSheet()
            .replace(MIKU_CYAN, GREEN)
            .replace("57,197,187", "166,227,161")
        )
        self._focus_prompt()

    # ── enviar ───────────────────────────────────────────────────────
    def _send(self):
        text = self.input_field.text().strip()
        if not text or self._is_generating: return

        full = text
        if self._attached_file and os.path.exists(self._attached_file):
            full = self._build_prompt(text, self._attached_file)
            self._attached_file = None
            # reset color del botón adjuntar
            self.btn_attach.setStyleSheet(
                _make_btn(self.btn_attach.parent(), "x").styleSheet())

        self._add_user_message(text)
        self.input_field.clear()

        self._generation_id += 1
        gen = self._generation_id
        self._is_generating  = True
        self._stop_requested = False
        self._messages.append({"role": "assistant", "text": "", "state": "typing"})
        self._render_chat()

        self.btn_send.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_attach.setEnabled(False)

        threading.Thread(target=self._fetch, args=(gen, full),
                         daemon=True).start()

    def _build_prompt(self, text, path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)
        except Exception as exc:
            self._add_system_message(f"No pude leer el archivo: {exc}")
            return text
        return (
            f"El usuario adjuntó '{os.path.basename(path)}':\n"
            f"```\n{content}\n```\n\nPregunta: {text}"
        )

    # ── streaming ────────────────────────────────────────────────────
    def _fetch(self, gen, prompt):
        pieces, stopped, is_error = [], False, False
        
        # 1. Capturamos el tiempo exacto del sistema en este milisegundo
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        user_context = f"Tu usuario se identifica como {DISPLAY_NAME}. "
        location_context = (
            f"Su ubicación configurada es {DISPLAY_LOCATION}. "
            if DISPLAY_LOCATION else ""
        )
        system_prompt = (
            f"Eres Miku, una IA de asistencia tecnológica integrada en esta interfaz. "
            f"{user_context}{location_context}"
            f"La fecha y hora actual del sistema es: {now}. "
            f"Responde de manera clara, eficiente, amigable y directa."
        )

        try:
            with requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL, 
                    "prompt": prompt, 
                    "system": system_prompt,  # <--- AQUÍ INYECTAMOS EL CONTEXTO
                    "stream": True
                },
                stream=True, timeout=(10, 300),
            ) as resp:
                self._active_resp = resp
                if resp.status_code != 200:
                    is_error = True
                    pieces.append(f"Error {resp.status_code}: Ollama no respondió.")
                else:
                    for line in resp.iter_lines(decode_unicode=True):
                        if self._stop_requested:
                            stopped = True; break
                        if not line: continue
                        try:
                            payload = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        chunk = payload.get("response", "")
                        if chunk:
                            pieces.append(chunk)
                            self.chunk_received.emit(gen, chunk)
                        if payload.get("done"):
                            break
        except requests.exceptions.ConnectionError:
            is_error = True
            pieces = ["Sin conexión. Revisa: ollama serve"]
        except requests.exceptions.Timeout:
            is_error = True; pieces = ["Timeout: modelo tardó demasiado."]
        except Exception as exc:
            if self._stop_requested: stopped = True
            else: is_error = True; pieces = [f"Error: {exc}"]
        finally:
            self._active_resp = None
        self.response_finished.emit(gen, "".join(pieces).strip(), stopped, is_error)

    def _stop(self):
        if not self._is_generating: return
        self._stop_requested = True
        self.btn_stop.setEnabled(False)
        if self._active_resp:
            try: self._active_resp.close()
            except: pass

    def _clear(self):
        if self._is_generating:
            self._stop()
            self._generation_id += 1
            self._is_generating = False
        self._attached_file = None
        self._messages = []
        self.btn_send.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_attach.setEnabled(True)
        self._add_assistant_message(
            f"Memoria limpia. {self._greeting()}, {DISPLAY_NAME}. ¿Qué hacemos ahora?")
        self._focus_prompt()

    # ── slots ────────────────────────────────────────────────────────
    def _on_chunk(self, gen, chunk):
        if gen != self._generation_id or not self._messages: return
        last = self._messages[-1]
        if last["role"] != "assistant": return
        last["text"] += chunk
        last["state"] = "streaming"
        self._render_chat()

    def _on_response_finished(self, gen, text, stopped, is_error):
        if gen != self._generation_id or not self._messages: return
        last = self._messages[-1]
        if last["role"] == "assistant":
            if stopped:
                last["text"] = (text or last["text"] or "Detenido.").rstrip() \
                               + "\n\n[Detenido por el usuario.]"
            else:
                last["text"] = text or last["text"] or "Sin contenido del modelo."
            last["state"] = "error" if is_error else "done"
        self._is_generating  = False
        self._stop_requested = False
        self.btn_send.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_attach.setEnabled(True)
        self._render_chat()
        self._focus_prompt()

    def _add_user_message(self, text):
        self._messages.append({"role": "user",      "text": text, "state": "done"})
        self._render_chat()

    def _add_assistant_message(self, text):
        self._messages.append({"role": "assistant", "text": text, "state": "done"})
        self._render_chat()

    def _add_system_message(self, text):
        self._messages.append({"role": "system",    "text": text, "state": "done"})
        self._render_chat()

    # ── render HTML ──────────────────────────────────────────────────
    def _render_chat(self):
        parts = [
            "<html><head><style>",
            "body{background:transparent;color:#d7def8;"
            "font-family:Consolas,monospace;margin:0;padding:0;}",
            ".msg{margin:3px 0;padding:5px 8px;border-radius:6px;line-height:1.38;}",
            ".ai {background:rgba(57,197,187,0.10);"
            "border:1px solid rgba(57,197,187,0.24);}",
            ".usr{background:rgba(30,144,255,0.12);"
            "border:1px solid rgba(30,144,255,0.24);text-align:right;}",
            ".sys{color:#a6e3a1;background:rgba(166,227,161,0.08);"
            "border:1px solid rgba(166,227,161,0.20);}",
            ".nm{font-weight:800;} .ty{color:#8b95b5;font-style:italic;}",
            "</style></head><body>",
        ]
        for msg in self._messages:
            role, text, state = (msg["role"],
                                  self._fmt(msg["text"]),
                                  msg.get("state", "done"))
            if role == "assistant":
                if not text and state == "typing":
                    text = "<span class='ty'>Procesando respuesta local…</span>"
                elif state in ("typing", "streaming") and text:
                    text += "<span class='ty'> ▌</span>"
                parts.append(
                    f"<div class='msg ai'>"
                    f"<span class='nm' style='color:{MIKU_CYAN};'>MIKU.AI:</span>"
                    f" {text}</div>")
            elif role == "user":
                parts.append(
                    f"<div class='msg usr'>"
                    f"<span class='nm' style='color:{MIKU_BLUE};'>TÚ:</span>"
                    f" {text}</div>")
            else:
                parts.append(f"<div class='msg sys'>{text}</div>")
        parts.append("</body></html>")
        self.chat.setHtml("".join(parts))
        QTimer.singleShot(0, lambda: self.chat.verticalScrollBar().setValue(
            self.chat.verticalScrollBar().maximum()))

    @staticmethod
    def _fmt(t):
        return html.escape(t).replace("\n", "<br>")

    # ── eventos de ventana ───────────────────────────────────────────
    def showEvent(self, e):
        self.input_field.setFocus()
        self._reposition_controls()
        super().showEvent(e)

    def closeEvent(self, e):
        if self._is_generating: self._stop()
        super().closeEvent(e)

    def changeEvent(self, e):
        if e.type() == QEvent.Type.WindowStateChange:
            self.btn_max.setText("❐" if self.isMaximized() else "□")
        super().changeEvent(e)

    # Drag sin barra de título
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (e.globalPosition().toPoint()
                              - self.frameGeometry().topLeft())
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and not self.isMaximized():
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MikuAIPopup()
    win.show()
    sys.exit(app.exec())
