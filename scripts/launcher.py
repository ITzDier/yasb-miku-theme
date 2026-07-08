"""Miku Cosmic Search — a transparent, keyboard-first Windows launcher."""

from __future__ import annotations

import ast
import json
import math
import operator
import os
import random
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QFileInfo,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QBrush,
    QCursor,
    QFont,
    QIcon,
    QKeyEvent,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
)
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import (
    QApplication,
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)


APP_DIR = Path(__file__).resolve().parent.parent
ASSET_DIR = APP_DIR / "assets"
STATE_FILE = APP_DIR / "scripts" / "launcher_recent.json"
SERVER_NAME = "MikuCosmicSearch_v3"

CYAN = QColor("#00F5D4")
PINK = QColor("#FF4FD8")
PURPLE = QColor("#A855F7")
INK = QColor("#EAFBFF")
MUTED = QColor("#75A9B9")


@dataclass
class SearchItem:
    name: str
    target: str
    kind: str = "APLICACIÓN"
    detail: str = ""
    icon_path: str = ""
    score: float = 0.0


def safe_calculate(expression: str) -> float | int | None:
    """Evaluate arithmetic only; no names, calls, indexing, or attributes."""
    allowed_binary = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    allowed_unary = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_binary:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError
            return allowed_binary[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary:
            return allowed_unary[type(node.op)](evaluate(node.operand))
        raise ValueError

    text = expression.strip().replace("×", "*").replace("÷", "/")
    if not text or len(text) > 80 or not any(char.isdigit() for char in text):
        return None
    try:
        value = evaluate(ast.parse(text, mode="eval"))
        if isinstance(value, (int, float)) and math.isfinite(value):
            return round(value, 10) if isinstance(value, float) else value
    except (ArithmeticError, SyntaxError, TypeError, ValueError):
        return None
    return None


class GradientLabel(QLabel):
    """Crisp text filled with the Miku pink-purple-cyan spectrum."""

    def paintEvent(self, event):
        if not self.text():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = self.font()
        painter.setFont(font)
        metrics = painter.fontMetrics()
        baseline = (self.height() + metrics.ascent() - metrics.descent()) / 2
        path = QPainterPath()
        path.addText(0, baseline, font, self.text())
        text_width = max(70, metrics.horizontalAdvance(self.text()))
        gradient = QLinearGradient(0, 0, text_width, 0)
        gradient.setColorAt(0.0, PINK)
        gradient.setColorAt(0.48, PURPLE)
        gradient.setColorAt(1.0, CYAN)
        outline = QPen(QColor(1, 3, 10, 245), 3.8)
        outline.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.strokePath(path, outline)
        painter.fillPath(path, gradient)


class OutlinedLabel(QLabel):
    """Solid text with a dark contour that survives bright and dark wallpapers."""

    def __init__(self, text="", color=INK, stroke=2.2, parent=None):
        super().__init__(text, parent)
        self.text_color = QColor(color)
        self.stroke_width = stroke

    def paintEvent(self, event):
        if not self.text():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = self.font()
        painter.setFont(font)
        metrics = painter.fontMetrics()
        bounds = self.contentsRect()
        text_width = metrics.horizontalAdvance(self.text())
        alignment = self.alignment()
        if alignment & Qt.AlignmentFlag.AlignRight:
            x = bounds.right() - text_width
        elif alignment & Qt.AlignmentFlag.AlignHCenter:
            x = bounds.left() + (bounds.width() - text_width) / 2
        else:
            x = bounds.left()
        baseline = bounds.top() + (bounds.height() + metrics.ascent() - metrics.descent()) / 2
        path = QPainterPath()
        path.addText(x, baseline, font, self.text())
        outline = QPen(QColor(1, 3, 10, 245), self.stroke_width)
        outline.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.strokePath(path, outline)
        painter.fillPath(path, self.text_color)


class CosmicSearchBox(QLineEdit):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(CYAN if self.hasFocus() else QColor(0, 245, 212, 150), 1.5)
        painter.setPen(pen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 23, 23)
        painter.setPen(QPen(PINK, 2))
        painter.drawLine(24, rect.bottom() - 1, 112, rect.bottom() - 1)
        painter.setPen(QPen(CYAN, 2))
        painter.drawEllipse(QPointF(25, self.height() / 2 - 1), 7, 7)
        painter.drawLine(
            QPointF(30, self.height() / 2 + 5),
            QPointF(36, self.height() / 2 + 11),
        )


class ResultRow(QFrame):
    activated = pyqtSignal(object)

    def __init__(self, item: SearchItem, icon: QIcon, parent=None):
        super().__init__(parent)
        self.item = item
        self.selected = False
        self.setObjectName("ResultRow")
        self.setFixedHeight(66)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 16, 8)
        layout.setSpacing(15)

        icon_label = QLabel()
        icon_label.setObjectName("AppIcon")
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(icon.pixmap(QSize(38, 38)))
        layout.addWidget(icon_label)

        words = QVBoxLayout()
        words.setSpacing(1)
        name = GradientLabel(item.name)
        name.setFont(QFont("Segoe UI Variable Display", 12, QFont.Weight.DemiBold))
        name.setMinimumHeight(26)
        words.addWidget(name)
        detail = OutlinedLabel(item.detail or item.kind, CYAN, 2.5)
        detail.setObjectName("ResultDetail")
        words.addWidget(detail)
        layout.addLayout(words, 1)

        kind = OutlinedLabel(item.kind, CYAN, 2.5)
        kind.setObjectName("KindBadge")
        kind.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(kind)
        self.refresh_style()

    def refresh_style(self):
        if self.selected:
            self.setStyleSheet(
                "QFrame#ResultRow { background: rgba(0,245,212,18); "
                "border: 1px solid rgba(0,245,212,225); border-radius: 19px; }"
            )
        else:
            self.setStyleSheet(
                "QFrame#ResultRow { background: transparent; "
                "border: 1px solid rgba(123,44,191,95); border-radius: 19px; }"
                "QFrame#ResultRow:hover { background: rgba(255,79,216,15); "
                "border-color: rgba(255,79,216,180); }"
            )

    def set_selected(self, selected: bool):
        self.selected = selected
        self.refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.item)
        super().mousePressEvent(event)


class CosmicCanvas(QWidget):
    """Animated edge particles and holographic outlines; never paints a fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.phase = 0.0
        random.seed(39)
        self.stars = [(random.random(), random.random(), random.random()) for _ in range(42)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)

    def tick(self):
        self.phase = (self.phase + 0.018) % (math.pi * 2)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = self.rect().adjusted(11, 11, -11, -11)
        rounded_frame = QPainterPath()
        rounded_frame.addRoundedRect(QRectF(outer), 43, 43)

        for width, alpha in ((10, 18), (5, 30), (1.6, 230)):
            gradient = QLinearGradient(QPointF(outer.topLeft()), QPointF(outer.bottomRight()))
            gradient.setColorAt(0.0, QColor(0, 245, 212, alpha))
            gradient.setColorAt(0.48, QColor(168, 85, 247, alpha))
            gradient.setColorAt(1.0, QColor(255, 79, 216, alpha))
            painter.setPen(QPen(QBrush(gradient), width))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(rounded_frame)

        # Stars hug the perimeter so the center remains easy to read.
        for px, py, seed in self.stars:
            if 0.09 < px < 0.91 and 0.10 < py < 0.90:
                continue
            pulse = 0.52 + 0.48 * math.sin(self.phase * 2 + seed * 9)
            color = CYAN if seed > 0.45 else PINK
            color.setAlpha(int(70 + pulse * 150))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            radius = 0.8 + pulse * 1.3
            painter.drawEllipse(QPointF(px * self.width(), py * self.height()), radius, radius)

        # Orbit marker in the upper-right corner.
        orbit = QRectF(self.width() - 104, 22, 62, 62)
        painter.setPen(QPen(QColor(168, 85, 247, 155), 1))
        painter.drawArc(orbit, int((30 + self.phase * 40) * 16), 220 * 16)
        angle = self.phase * 1.5
        center = orbit.center()
        point = QPointF(center.x() + math.cos(angle) * 31, center.y() + math.sin(angle) * 31)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(PINK)
        painter.drawEllipse(point, 3, 3)


class MikuCosmicLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.icon_provider = QFileIconProvider()
        self.items = self.build_index()
        self.recents = self.load_recents()
        self.rows: list[ResultRow] = []
        self.selected_index = 0
        self.drag_offset: QPoint | None = None
        self.can_auto_hide = False
        self.init_ui()
        self.populate("")

    def init_ui(self):
        self.setObjectName("Launcher")
        self.setWindowTitle("Miku Cosmic Search")
        self.setWindowIcon(QIcon(str(ASSET_DIR / "Miku_Tie.png")))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(790, 610)

        root = QVBoxLayout(self)
        root.setContentsMargins(31, 27, 31, 27)
        root.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(9, 2, 18, 9)
        tie = QLabel()
        tie.setFixedSize(28, 48)
        tie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tie_pixmap = QPixmap(str(ASSET_DIR / "Miku_Tie.png"))
        if not tie_pixmap.isNull():
            tie.setPixmap(
                tie_pixmap.scaled(
                    22,
                    44,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        header.addWidget(tie)
        header.addSpacing(6)
        brand = QVBoxLayout()
        brand.setSpacing(0)
        title = GradientLabel("MIKU // COSMIC SEARCH")
        title.setFont(QFont("Segoe UI Variable Display", 16, QFont.Weight.Bold))
        title.setMinimumHeight(34)
        title.setMinimumWidth(340)
        brand.addWidget(title)
        subtitle = OutlinedLabel(
            "NEURAL APPLICATION MATRIX  ·  WINDOWS LINK ONLINE",
            QColor("#9BDDE8"),
            1.8,
        )
        subtitle.setObjectName("Subtitle")
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        live = QLabel("●  LIVE")
        live.setObjectName("LiveBadge")
        header.addWidget(live)
        root.addLayout(header)

        self.search = CosmicSearchBox()
        self.search.setObjectName("SearchBox")
        self.search.setPlaceholderText("Busca una aplicación, archivo o escribe una operación…")
        self.search.setFixedHeight(58)
        self.search.setTextMargins(48, 0, 28, 0)
        search_palette = self.search.palette()
        search_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#D8F8FF"))
        self.search.setPalette(search_palette)
        self.search.textChanged.connect(self.populate)
        self.search.installEventFilter(self)
        root.addWidget(self.search)
        root.addSpacing(10)

        info = QHBoxLayout()
        info.setContentsMargins(7, 0, 7, 5)
        self.counter = OutlinedLabel("", QColor("#A9EAF0"), 1.8)
        self.counter.setObjectName("Counter")
        info.addWidget(self.counter)
        info.addStretch()
        shortcut = OutlinedLabel(
            "↑↓  NAVEGAR     ENTER  ABRIR     ESC  CERRAR",
            QColor("#A9EAF0"),
            1.8,
        )
        shortcut.setObjectName("Shortcut")
        info.addWidget(shortcut)
        root.addLayout(info)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("ResultsScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.result_host = QWidget()
        self.result_host.setObjectName("ResultHost")
        self.result_layout = QVBoxLayout(self.result_host)
        self.result_layout.setContentsMargins(1, 1, 1, 1)
        self.result_layout.setSpacing(7)
        self.result_layout.addStretch()
        self.scroll.setWidget(self.result_host)
        root.addWidget(self.scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(7, 9, 7, 0)
        status = OutlinedLabel("初音ミク  ·  SYSTEM 39", PINK, 1.8)
        status.setObjectName("FooterMiku")
        footer.addWidget(status)
        footer.addStretch()
        self.clock = OutlinedLabel("", CYAN, 1.8)
        self.clock.setObjectName("FooterClock")
        footer.addWidget(self.clock)
        root.addLayout(footer)

        self.canvas = CosmicCanvas(self)
        self.canvas.raise_()

        self.setStyleSheet(
            """
            QWidget#Launcher, QWidget#ResultHost { background: transparent; }
            QLabel#Subtitle { color: rgba(117,169,185,210); font-family: 'Consolas';
                font-size: 9px; letter-spacing: 2px; }
            QLabel#LiveBadge { color: #00F5D4; font-family: 'Consolas'; font-size: 10px;
                border: 1px solid rgba(0,245,212,140); border-radius: 9px; padding: 3px 9px;
                background: rgba(0,245,212,10); }
            QLineEdit#SearchBox { color: #FFFFFF; background: rgba(3,8,20,105);
                border: none; border-radius: 16px; font-family: 'Segoe UI Variable Display';
                font-size: 17px; font-weight: 600;
                selection-background-color: rgba(255,79,216,175); }
            QLabel#Counter, QLabel#Shortcut { color: rgba(117,169,185,215);
                font-family: 'Consolas'; font-size: 9px; letter-spacing: 1px; }
            QLabel#ResultDetail { color: rgba(117,169,185,220); font-family: 'Consolas';
                font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QLabel#KindBadge { color: rgba(0,245,212,190); font-family: 'Consolas';
                font-size: 10px; font-weight: 800; letter-spacing: 1px; }
            QLabel#FooterMiku { color: rgba(255,79,216,210); font-family: 'Consolas';
                font-size: 9px; letter-spacing: 1px; }
            QLabel#FooterClock { color: rgba(0,245,212,210); font-family: 'Consolas';
                font-size: 9px; letter-spacing: 1px; }
            QScrollArea#ResultsScroll { background: transparent; border: none; }
            QScrollBar:vertical { background: transparent; width: 3px; margin: 3px 0; }
            QScrollBar::handle:vertical { background: rgba(0,245,212,135); min-height: 28px;
                border-radius: 1px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            """
        )
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

    def resizeEvent(self, event):
        self.canvas.setGeometry(self.rect())
        super().resizeEvent(event)

    def update_clock(self):
        self.clock.setText(time.strftime("%H:%M:%S  //  %d.%m.%Y"))

    def show_launcher(self):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        self.move(area.center().x() - self.width() // 2, area.top() + 66)
        self.can_auto_hide = False
        self.show()
        self.raise_()
        self.activateWindow()
        self.search.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self.search.selectAll()
        self.setWindowOpacity(0.0)
        self.fade = QPropertyAnimation(self, b"windowOpacity", self)
        self.fade.setDuration(190)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self.fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade.start()
        QTimer.singleShot(450, lambda: setattr(self, "can_auto_hide", True))

    def toggle(self):
        if self.isVisible():
            self.close()
        else:
            self.show_launcher()

    def event(self, event):
        if event.type() == QEvent.Type.WindowDeactivate and self.can_auto_hide:
            QTimer.singleShot(90, self.hide_if_inactive)
        return super().event(event)

    def hide_if_inactive(self):
        if self.can_auto_hide and not self.isActiveWindow():
            self.close()

    def eventFilter(self, watched, event):
        if watched is self.search and event.type() == QEvent.Type.KeyPress:
            key_event: QKeyEvent = event
            if key_event.key() == Qt.Key.Key_Down:
                self.move_selection(1)
                return True
            if key_event.key() == Qt.Key.Key_Up:
                self.move_selection(-1)
                return True
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.activate_selected()
                return True
            if key_event.key() == Qt.Key.Key_Escape:
                self.close()
                return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 78:
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_offset and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        super().mouseReleaseEvent(event)

    def build_index(self) -> list[SearchItem]:
        roots = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
            Path(os.environ.get("PROGRAMDATA", Path(Path.home().anchor) / "ProgramData"))
            / "Microsoft/Windows/Start Menu/Programs",
        ]
        found: dict[str, SearchItem] = {}
        for root in roots:
            if not root.exists():
                continue
            for pattern in ("*.lnk", "*.url", "*.appref-ms"):
                try:
                    paths = root.rglob(pattern)
                    for path in paths:
                        name = path.stem.strip()
                        key = name.casefold()
                        if not name or key in found or "uninstall" in key or "desinstalar" in key:
                            continue
                        category = path.parent.name if path.parent != root else "Windows"
                        found[key] = SearchItem(
                            name=name,
                            target=str(path),
                            detail=category.upper(),
                            icon_path=str(path),
                        )
                except OSError:
                    continue

        system = [
            ("Explorador de archivos", "explorer.exe", "SISTEMA", "explorer.exe"),
            ("Configuración", "ms-settings:", "SISTEMA", "shell32.dll"),
            ("Terminal", "wt.exe", "SISTEMA", "wt.exe"),
            ("Administrador de tareas", "taskmgr.exe", "SISTEMA", "taskmgr.exe"),
            ("Panel de control", "control.exe", "SISTEMA", "control.exe"),
            ("Calculadora", "calc.exe", "SISTEMA", "calc.exe"),
        ]
        for name, target, detail, icon in system:
            found.setdefault(name.casefold(), SearchItem(name, target, "SISTEMA", detail, icon))
        return sorted(found.values(), key=lambda item: item.name.casefold())

    def load_recents(self) -> dict[str, dict]:
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_recent(self, item: SearchItem):
        if item.kind not in ("APLICACIÓN", "SISTEMA"):
            return
        record = self.recents.get(item.target, {"count": 0})
        record.update({"name": item.name, "count": record.get("count", 0) + 1, "time": time.time()})
        self.recents[item.target] = record
        try:
            STATE_FILE.write_text(json.dumps(self.recents, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    @staticmethod
    def match_score(name: str, query: str) -> float:
        name = name.casefold()
        query = query.casefold().strip()
        if not query:
            return 0
        if name == query:
            return 1000
        if name.startswith(query):
            return 800 - len(name) * 0.1
        words = name.replace("-", " ").replace("_", " ").split()
        if any(word.startswith(query) for word in words):
            return 650 - len(name) * 0.1
        if query in name:
            return 500 - name.index(query) * 3
        # Ordered fuzzy subsequence: forgiving but deterministic.
        cursor = 0
        gaps = 0
        for char in query:
            position = name.find(char, cursor)
            if position < 0:
                return -1
            gaps += position - cursor
            cursor = position + 1
        return 280 - gaps * 4 - (len(name) - len(query))

    def search_items(self, query: str) -> list[SearchItem]:
        query = query.strip()
        if not query:
            recent_order = sorted(
                self.items,
                key=lambda item: (
                    -self.recents.get(item.target, {}).get("time", 0),
                    -self.recents.get(item.target, {}).get("count", 0),
                    item.name.casefold(),
                ),
            )
            return recent_order[:6]

        results = []
        for item in self.items:
            score = self.match_score(item.name, query)
            if score >= 0:
                item.score = score + min(50, self.recents.get(item.target, {}).get("count", 0) * 3)
                results.append(item)
        results.sort(key=lambda item: (-item.score, item.name.casefold()))

        calculated = safe_calculate(query)
        if calculated is not None:
            results.insert(
                0,
                SearchItem(str(calculated), f"copy:{calculated}", "CALCULADORA", f"{query}  ·  ENTER PARA COPIAR"),
            )
        path = Path(os.path.expandvars(query.strip('"')))
        if path.exists():
            results.insert(0, SearchItem(path.name or str(path), str(path), "ARCHIVO", str(path), str(path)))

        encoded = urllib.parse.quote(query)
        results.append(
            SearchItem(
                f'Buscar “{query}” en tus archivos',
                f"search-ms:query={encoded}",
                "ARCHIVOS",
                "ÍNDICE DE WINDOWS",
            )
        )
        results.append(
            SearchItem(
                f'Buscar “{query}” en la web',
                f"https://www.google.com/search?q={encoded}",
                "WEB",
                "NAVEGADOR PREDETERMINADO",
            )
        )
        return results[:8]

    def item_icon(self, item: SearchItem) -> QIcon:
        if item.kind == "WEB":
            return self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        if item.kind == "CALCULADORA":
            return self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        if item.kind == "ARCHIVOS":
            return self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        source = Path(item.icon_path) if item.icon_path else None
        if source and source.exists():
            icon = self.icon_provider.icon(QFileInfo(str(source)))
            if not icon.isNull():
                return icon
        if item.target.startswith("ms-settings"):
            return self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        return self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    def clear_results(self):
        self.rows.clear()
        while self.result_layout.count():
            child = self.result_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()

    def populate(self, query: str):
        results = self.search_items(query)
        self.clear_results()
        label = "SUGERENCIAS RECIENTES" if not query.strip() else f"{len(results)} COINCIDENCIAS"
        self.counter.setText(label)
        for item in results:
            row = ResultRow(item, self.item_icon(item))
            row.activated.connect(self.launch)
            self.result_layout.addWidget(row)
            self.rows.append(row)
        self.result_layout.addStretch()
        self.selected_index = 0
        self.refresh_selection()
        self.scroll.verticalScrollBar().setValue(0)

    def move_selection(self, direction: int):
        if not self.rows:
            return
        self.selected_index = (self.selected_index + direction) % len(self.rows)
        self.refresh_selection()
        self.scroll.ensureWidgetVisible(self.rows[self.selected_index], 0, 14)

    def refresh_selection(self):
        for index, row in enumerate(self.rows):
            row.set_selected(index == self.selected_index)

    def activate_selected(self):
        if self.rows:
            self.launch(self.rows[self.selected_index].item)

    def launch(self, item: SearchItem):
        try:
            if item.target.startswith("copy:"):
                QApplication.clipboard().setText(item.target[5:])
                self.search.setText(item.target[5:])
                self.search.selectAll()
                return
            self.save_recent(item)
            os.startfile(item.target)
            self.close()
        except OSError:
            try:
                subprocess.Popen([item.target], creationflags=subprocess.CREATE_NO_WINDOW)
                self.close()
            except OSError:
                self.counter.setText("NO SE PUDO ABRIR  ·  REVISA EL ACCESO")


def connect_to_existing() -> bool:
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(220):
        socket.write(b"toggle")
        socket.flush()
        socket.waitForBytesWritten(220)
        socket.disconnectFromServer()
        return True
    return False


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Miku Cosmic Search")
    app.setQuitOnLastWindowClosed(True)
    preview = "--preview" in sys.argv

    if not preview and connect_to_existing():
        return 0

    server = QLocalServer()
    QLocalServer.removeServer(SERVER_NAME)
    server.listen(SERVER_NAME)
    launcher = MikuCosmicLauncher()

    def receive_command():
        connection = server.nextPendingConnection()
        if connection:
            connection.waitForReadyRead(120)
            launcher.toggle()
            connection.disconnectFromServer()

    server.newConnection.connect(receive_command)
    launcher.show_launcher()

    if preview:
        def capture_preview():
            QApplication.processEvents()
            target = APP_DIR / ".launcher_preview.png"
            from PIL import ImageGrab

            box = (
                launcher.x(),
                launcher.y(),
                launcher.x() + launcher.width(),
                launcher.y() + launcher.height(),
            )
            ImageGrab.grab(bbox=box, all_screens=True).save(target)
            print(f"preview_saved=True path={target}", flush=True)
            app.quit()

        def prepare_preview():
            launcher.search.setText("visual studio")
            QTimer.singleShot(300, capture_preview)

        QTimer.singleShot(700, prepare_preview)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
