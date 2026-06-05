import math

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QSlider, QSizePolicy, QFileDialog,
    QMessageBox, QProgressDialog, QDialog, QButtonGroup, QSizeGrip,
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QRect, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPainterPath, QLinearGradient, QFont,
    QPen, QBrush, QRadialGradient, QMouseEvent, QFontMetrics,
)

from ui.search_panel import SearchPanel
from ui.result_card import ResultCard
from ui.queue_panel import QueuePanel
from ui.settings_dialog import SettingsDialog
from core.search import SearchWorker
from core.preview import PreviewWorker, Player
from core.spotify import SpotifyImportWorker
import config

# ── colour tokens ──────────────────────────────────────────────────────────────
INK        = "#221C2B"
INK_2      = "#6E6577"
PAPER      = "#FAF6F2"
LINE       = "#ECE3DC"
SURFACE_2  = "#F0E8E4"
CORAL      = "#FF82A8"
CORAL_DEEP = "#E85684"
DOCK_BASE  = "#211B30"
DOCK_TOP   = "#2C2541"
DOCK_3     = "#3A3253"
DOCK_INK   = "#EBE6F2"
DOCK_INK2  = "#A49CB8"


def _fmt_time(ms: int) -> str:
    s = max(0, ms // 1000)
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"


# ══════════════════════════════════════════════════════════════════════════════
#  WaveformWidget
# ══════════════════════════════════════════════════════════════════════════════

class WaveformWidget(QWidget):
    seeked = pyqtSignal(float)  # 0.0–1.0

    _BAR_W = 3
    _GAP   = 2
    _BARS  = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pos = 0.0
        self.setFixedHeight(34)
        self.setMinimumWidth(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._heights = [
            max(4, int(8 + 22 * abs(math.sin(i / self._BARS * math.pi * 5 + 0.3))
                           * (0.5 + 0.5 * abs(math.cos(i / self._BARS * math.pi * 2.5)))))
            for i in range(self._BARS)
        ]

    def set_position(self, frac: float):
        self._pos = max(0.0, min(1.0, frac))
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        total_w = self._BARS * (self._BAR_W + self._GAP) - self._GAP
        ox = max(0, (w - total_w) // 2)
        playhead = int(self._pos * self._BARS)

        for i in range(self._BARS):
            bh = min(self._heights[i], h - 4)
            x = ox + i * (self._BAR_W + self._GAP)
            y = (h - bh) // 2
            c = QColor(CORAL) if i < playhead else QColor(255, 255, 255, 55)
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x, y, self._BAR_W, bh, 1.5, 1.5)

        # playhead dot
        px = ox + playhead * (self._BAR_W + self._GAP)
        p.setBrush(QColor("white"))
        p.drawEllipse(px - 3, h // 2 - 3, 6, 6)

    def mousePressEvent(self, e: QMouseEvent):
        self._seek(e.position().x())

    def mouseMoveEvent(self, e: QMouseEvent):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self._seek(e.position().x())

    def _seek(self, x: float):
        total_w = self._BARS * (self._BAR_W + self._GAP) - self._GAP
        ox = max(0, (self.width() - total_w) // 2)
        frac = max(0.0, min(1.0, (x - ox) / total_w))
        self._pos = frac
        self.update()
        self.seeked.emit(frac)


# ══════════════════════════════════════════════════════════════════════════════
#  TitleBar helpers
# ══════════════════════════════════════════════════════════════════════════════

class _TrafficLight(QPushButton):
    _C = {"red": "#FF5F56", "yellow": "#FFBD2E", "green": "#27C93F"}
    _G = {"red": "×", "yellow": "−", "green": "+"}

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._color = QColor(self._C[role])
        self._glyph = self._G[role]
        self._hov = False
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet("background: transparent; border: none;")

    def enterEvent(self, _e):  self._hov = True;  self.update()
    def leaveEvent(self, _e):  self._hov = False; self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self._color.darker(115) if self._hov else self._color
        p.setBrush(c)
        p.setPen(QPen(c.darker(130), 0.5))
        p.drawEllipse(0, 0, 13, 13)
        if self._hov:
            p.setPen(QColor(0, 0, 0, 180))
            f = QFont()
            f.setPixelSize(9)
            f.setBold(True)
            p.setFont(f)
            p.drawText(QRect(0, 0, 13, 13), Qt.AlignmentFlag.AlignCenter, self._glyph)


class _BrandMark(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QRadialGradient(12, 12, 12)
        g.setColorAt(0.0, QColor("white"))
        g.setColorAt(0.55, QColor(CORAL))
        g.setColorAt(1.0,  QColor(INK))
        p.setBrush(g)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 24, 24)


class _OutputChip(QWidget):
    clicked = pyqtSignal()

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setMaximumWidth(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"_OutputChip {{ background: {SURFACE_2}; border-radius: 999px; border: 1px solid {LINE}; }}"
            f"_OutputChip:hover {{ background: {LINE}; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(5)
        dot = QLabel("●")
        dot.setStyleSheet("color: #1DB954; font-size: 8px; background: transparent;")
        lay.addWidget(dot)
        self._lbl = QLabel()
        self._lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono', monospace; font-size: 11px; "
            f"color: {INK}; background: transparent;"
        )
        lay.addWidget(self._lbl)
        self.set_path(path)

    def set_path(self, path: str):
        display = (path.split("/")[-1] or path or "No folder set")
        fm = QFontMetrics(self._lbl.font())
        self._lbl.setText(fm.elidedText(display, Qt.TextElideMode.ElideRight, 140))
        self._lbl.setToolTip(path)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class _SegCtrl(QWidget):
    changed = pyqtSignal(int)

    def __init__(self, options: list[str], parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(
            f"_SegCtrl {{ background: {SURFACE_2}; border-radius: 999px; }}"
        )
        lay = QHBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(2, 2, 2, 2)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for i, txt in enumerate(options):
            b = QPushButton(txt)
            b.setCheckable(True)
            b.setChecked(i == 0)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self._group.addButton(b, i)
            lay.addWidget(b)
            b.setStyleSheet(self._style(i == 0))
        self._group.idToggled.connect(self._toggle)

    def _style(self, active: bool) -> str:
        if active:
            return (
                "QPushButton { background: white; border: none; border-radius: 999px; "
                f"color: {INK}; font-size: 12px; font-weight: 600; padding: 2px 11px; }}"
            )
        return (
            "QPushButton { background: transparent; border: none; border-radius: 999px; "
            f"color: {INK_2}; font-size: 12px; padding: 2px 11px; }}"
            f"QPushButton:hover {{ color: {INK}; }}"
        )

    def _toggle(self, btn_id: int, checked: bool):
        if checked:
            for i, b in enumerate(self._group.buttons()):
                b.setStyleSheet(self._style(self._group.id(b) == btn_id))
            self.changed.emit(btn_id)

    def current_index(self) -> int:
        return self._group.checkedId()

    def set_index(self, idx: int):
        btn = self._group.button(idx)
        if btn:
            btn.setChecked(True)


class _BadgeBtn(QPushButton):
    def __init__(self, icon_text: str, parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ background: {SURFACE_2}; border: none; border-radius: 18px; "
            f"color: {INK}; font-size: 15px; }}"
            f"QPushButton:hover {{ background: {LINE}; }}"
        )
        self._badge = QLabel("0", self)
        self._badge.setFixedSize(16, 16)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setStyleSheet(
            f"background: {CORAL}; color: white; font-size: 9px; font-weight: 700; "
            "border-radius: 8px;"
        )
        self._badge.move(22, 0)
        self._badge.hide()

    def set_badge(self, n: int):
        if n > 0:
            self._badge.setText(str(n))
            self._badge.show()
        else:
            self._badge.hide()


# ══════════════════════════════════════════════════════════════════════════════
#  TitleBar
# ══════════════════════════════════════════════════════════════════════════════

class TitleBar(QWidget):
    output_dir_changed = pyqtSignal(str)
    format_changed     = pyqtSignal(str)
    settings_requested = pyqtSignal()
    queue_toggled      = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_pos = None
        self._output_dir = config.get("output_dir") or ""
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 12, 0)
        lay.setSpacing(10)

        # Traffic lights
        tl = QHBoxLayout()
        tl.setSpacing(7)
        tl.setContentsMargins(0, 0, 0, 0)
        self._red    = _TrafficLight("red")
        self._yellow = _TrafficLight("yellow")
        self._green  = _TrafficLight("green")
        for w in (self._red, self._yellow, self._green):
            tl.addWidget(w)
        lay.addLayout(tl)
        lay.addSpacing(10)

        lay.addWidget(_BrandMark())
        brand = QLabel("Jamdar")
        brand.setStyleSheet(
            f"font-family: 'Bricolage Grotesque 96pt ExtraBold', sans-serif; font-size: 15px; "
            f"font-weight: 600; color: {INK}; background: transparent; letter-spacing: -0.3px;"
        )
        lay.addWidget(brand)
        lay.addStretch()

        self._chip = _OutputChip(self._output_dir)
        self._chip.clicked.connect(self._browse)
        lay.addWidget(self._chip)
        lay.addSpacing(8)

        self._fmt = _SegCtrl(["MP3", "FLAC"])
        saved = config.get("default_format") or "mp3"
        self._fmt.set_index(0 if saved == "mp3" else 1)
        self._fmt.changed.connect(self._on_fmt)
        lay.addWidget(self._fmt)
        lay.addSpacing(8)

        self._dl_btn = _BadgeBtn("↓")
        self._dl_btn.clicked.connect(self.queue_toggled)
        lay.addWidget(self._dl_btn)

        gear = QPushButton("⚙")
        gear.setFixedSize(36, 36)
        gear.setToolTip("Settings")
        gear.setCursor(Qt.CursorShape.PointingHandCursor)
        gear.setStyleSheet(
            f"QPushButton {{ background: {SURFACE_2}; border: none; border-radius: 18px; "
            f"color: {INK}; font-size: 16px; }}"
            f"QPushButton:hover {{ background: {LINE}; }}"
        )
        gear.clicked.connect(self.settings_requested)
        lay.addWidget(gear)

    def wire_window(self, win: QMainWindow):
        self._red.clicked.connect(win.close)
        self._yellow.clicked.connect(win.showMinimized)
        self._green.clicked.connect(lambda: win.showNormal() if win.isMaximized() else win.showMaximized())

    def set_active_downloads(self, n: int):
        self._dl_btn.set_badge(n)

    def refresh_output(self):
        path = config.get("output_dir") or ""
        self._output_dir = path
        self._chip.set_path(path)

    def current_format(self) -> str:
        return "mp3" if self._fmt.current_index() == 0 else "flac"

    def _browse(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select output folder", self._output_dir or ""
        )
        if path:
            config.set("output_dir", path)
            self._output_dir = path
            self._chip.set_path(path)
            self.output_dir_changed.emit(path)

    def _on_fmt(self, idx: int):
        fmt = "mp3" if idx == 0 else "flac"
        config.set("default_format", fmt)
        self.format_changed.emit(fmt)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setPen(QPen(QColor(LINE), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            wh = win.windowHandle() if win else None
            if wh:
                wh.startSystemMove()
            else:
                self._drag_pos = e.globalPosition().toPoint() - win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QMouseEvent):
        if e.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _e):
        self._drag_pos = None


# ══════════════════════════════════════════════════════════════════════════════
#  NowPlayingDock
# ══════════════════════════════════════════════════════════════════════════════

class NowPlayingDock(QWidget):
    download_requested = pyqtSignal(dict, str)

    def __init__(self, player: Player, parent=None):
        super().__init__(parent)
        self._player = player
        self._duration_ms = 30_000
        self._paused = False
        self._current_result: dict | None = None
        self.setFixedHeight(96)
        self._build()
        self.hide()

        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._tick)

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 0, 22, 0)
        lay.setSpacing(20)

        # Meta (cover + text)
        meta = QWidget()
        meta.setFixedWidth(286)
        meta.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        ml = QHBoxLayout(meta)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(12)

        self._cover = QLabel()
        self._cover.setFixedSize(60, 60)
        self._cover.setStyleSheet(f"border-radius: 13px; background: {DOCK_3};")
        ml.addWidget(self._cover)

        tc = QVBoxLayout()
        tc.setSpacing(2)
        tc.setContentsMargins(0, 0, 0, 0)

        self._title = QLabel("—")
        self._title.setStyleSheet(
            f"font-family: 'Bricolage Grotesque 96pt ExtraBold', sans-serif; font-size: 15px; "
            f"font-weight: 700; color: {DOCK_INK}; background: transparent;"
        )
        tc.addWidget(self._title)

        self._sub = QLabel("")
        self._sub.setStyleSheet(
            f"font-size: 12px; color: {DOCK_INK2}; background: transparent;"
        )
        tc.addWidget(self._sub)

        tag = QLabel("PREVIEW")
        tag.setStyleSheet(
            f"font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: 700; "
            f"color: {CORAL}; background: rgba(255,130,168,.15); "
            "border-radius: 4px; padding: 2px 6px;"
        )
        tc.addWidget(tag)
        tc.addStretch()
        ml.addLayout(tc)
        lay.addWidget(meta)

        # Transport
        tr = QHBoxLayout()
        tr.setSpacing(8)
        tr.setContentsMargins(0, 0, 0, 0)

        restart = QPushButton("⏮")
        restart.setFixedSize(38, 38)
        restart.setToolTip("Restart")
        restart.setCursor(Qt.CursorShape.PointingHandCursor)
        restart.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {DOCK_INK2}; "
            f"font-size: 18px; border-radius: 19px; }}"
            f"QPushButton:hover {{ color: {DOCK_INK}; background: rgba(255,255,255,.08); }}"
        )
        restart.clicked.connect(lambda: self._player.set_position(0))
        tr.addWidget(restart)

        self._play_btn = QPushButton("⏸")
        self._play_btn.setFixedSize(52, 52)
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.setStyleSheet(
            f"QPushButton {{ background: {CORAL}; border: none; border-radius: 26px; "
            f"color: white; font-size: 20px; }}"
            f"QPushButton:hover {{ background: {CORAL_DEEP}; }}"
        )
        self._play_btn.clicked.connect(self._toggle_pause)
        tr.addWidget(self._play_btn)

        stop = QPushButton("⏹")
        stop.setFixedSize(38, 38)
        stop.setToolTip("Stop preview")
        stop.setCursor(Qt.CursorShape.PointingHandCursor)
        stop.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {DOCK_INK2}; "
            f"font-size: 18px; border-radius: 19px; }}"
            f"QPushButton:hover {{ color: {DOCK_INK}; background: rgba(255,255,255,.08); }}"
        )
        stop.clicked.connect(self._stop)
        tr.addWidget(stop)
        lay.addLayout(tr)

        # Scrubber
        sc = QHBoxLayout()
        sc.setSpacing(10)
        sc.setContentsMargins(0, 0, 0, 0)

        self._curr_lbl = QLabel("0:00")
        self._curr_lbl.setStyleSheet(
            "font-family: 'JetBrains Mono', monospace; font-size: 11px; "
            "color: white; background: transparent; min-width: 34px;"
        )
        self._curr_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        sc.addWidget(self._curr_lbl)

        self._wave = WaveformWidget()
        self._wave.seeked.connect(self._on_seek)
        sc.addWidget(self._wave, stretch=1)

        self._total_lbl = QLabel("0:30")
        self._total_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono', monospace; font-size: 11px; "
            f"color: {DOCK_INK2}; background: transparent; min-width: 34px;"
        )
        sc.addWidget(self._total_lbl)
        lay.addLayout(sc, stretch=1)

        # Right: volume + download
        rr = QHBoxLayout()
        rr.setSpacing(8)
        rr.setContentsMargins(0, 0, 0, 0)

        vol_icon = QLabel("🔈")
        vol_icon.setStyleSheet(f"color: {DOCK_INK2}; background: transparent; font-size: 14px;")
        rr.addWidget(vol_icon)

        self._vol = QSlider(Qt.Orientation.Horizontal)
        self._vol.setRange(0, 100)
        self._vol.setValue(80)
        self._vol.setFixedWidth(62)
        self._vol.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 5px; background: rgba(255,255,255,.20); border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 12px; height: 12px; margin: -4px 0;
                background: white; border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #FF82A8; border-radius: 2px;
            }
        """)
        rr.addWidget(self._vol)

        dl_btn = QPushButton("↓ Download")
        dl_btn.setFixedHeight(34)
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.20); "
            "border-radius: 999px; color: white; font-size: 13px; font-weight: 600; padding: 0 16px; }"
            "QPushButton:hover { background: rgba(255,255,255,.22); }"
        )
        dl_btn.clicked.connect(self._on_download)
        rr.addWidget(dl_btn)
        lay.addLayout(rr)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0.0, QColor(DOCK_TOP))
        g.setColorAt(1.0, QColor(DOCK_BASE))
        p.fillRect(self.rect(), g)

    # ── public API ──

    def set_loading(self, result: dict):
        self._current_result = result
        title = result.get("title", "Loading…")
        self._title.setText(self._eln(title, 22))
        platform = result.get("platform", "")
        dot_char = "●"
        dot_color = "#FF3B30" if platform == "youtube" else "#FF5500" if platform == "soundcloud" else "#888"
        self._sub.setText(f"<font color='{dot_color}'>{dot_char}</font>  {platform.title()}")
        self._play_btn.setText("…")
        self._play_btn.setEnabled(False)
        self._wave.set_position(0.0)
        self._curr_lbl.setText("0:00")
        self.show()

    def set_duration(self, seconds: float):
        self._duration_ms = int(seconds * 1000)
        self._total_lbl.setText(_fmt_time(self._duration_ms))

    def set_ready(self, title: str):
        self._title.setText(self._eln(title, 22))
        self._play_btn.setText("⏸")
        self._play_btn.setEnabled(True)
        self._paused = False
        self._timer.start()

    def set_cover(self, pixmap):
        if pixmap and not pixmap.isNull():
            from PyQt6.QtCore import QRect as _QR
            scaled = pixmap.scaled(
                60, 60,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            if scaled.width() > 60 or scaled.height() > 60:
                x = (scaled.width() - 60) // 2
                y = (scaled.height() - 60) // 2
                scaled = scaled.copy(_QR(x, y, 60, 60))
            self._cover.setPixmap(scaled)

    # ── private ──

    def _tick(self):
        pos_ms = self._player.get_position_ms()
        self._curr_lbl.setText(_fmt_time(pos_ms))
        if self._duration_ms > 0:
            self._wave.set_position(pos_ms / self._duration_ms)
        if pos_ms >= 0 and not self._player.is_playing() and not self._player.is_paused():
            self._stop()

    def _toggle_pause(self):
        if self._paused:
            self._player.resume()
            self._play_btn.setText("⏸")
        else:
            self._player.pause()
            self._play_btn.setText("▶")
        self._paused = not self._paused

    def _on_seek(self, frac: float):
        self._player.set_position(frac * self._duration_ms / 1000.0)

    def _stop(self):
        self._timer.stop()
        self._player.stop()
        self.hide()

    def _on_download(self):
        if self._current_result:
            fmt = config.get("default_format") or "mp3"
            self.download_requested.emit(self._current_result, fmt)

    @staticmethod
    def _eln(text: str, max_chars: int) -> str:
        return text[:max_chars] + "…" if len(text) > max_chars + 1 else text


# ══════════════════════════════════════════════════════════════════════════════
#  MainWindow
# ══════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jamdar")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1280, 720)
        self.setMinimumSize(QSize(900, 600))

        self._search_worker: SearchWorker | None = None
        self._preview_worker: PreviewWorker | None = None
        self._preview_result: dict = {}
        self._player = Player()
        self._current_output_dir = config.get("output_dir") or ""
        self._current_format = config.get("default_format") or "mp3"

        self._build()
        self._load_stylesheet()

    # ── build ──

    def _build(self):
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # App shell (rounded, paper bg)
        self._shell = QWidget()
        self._shell.setObjectName("AppShell")
        self._shell.setStyleSheet(
            f"QWidget#AppShell {{ background: {PAPER}; border-radius: 32px; }}"
        )
        root.addWidget(self._shell)

        shell_layout = QVBoxLayout(self._shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        # Title bar
        self._titlebar = TitleBar()
        self._titlebar.wire_window(self)
        self._titlebar.output_dir_changed.connect(self._set_output_dir)
        self._titlebar.format_changed.connect(self._set_format)
        self._titlebar.settings_requested.connect(self._open_settings)
        self._titlebar.queue_toggled.connect(self._toggle_queue)
        shell_layout.addWidget(self._titlebar)

        # Search panel
        self._search_panel = SearchPanel()
        self._search_panel.search_requested.connect(self._on_search)
        self._search_panel.spotify_requested.connect(self._on_spotify_import)
        shell_layout.addWidget(self._search_panel)

        # Body: results (flex) + queue (330px fixed)
        body = QWidget()
        body.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # Results scroll
        results_outer = QWidget()
        results_outer.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        ro_lay = QVBoxLayout(results_outer)
        ro_lay.setContentsMargins(16, 12, 12, 12)
        ro_lay.setSpacing(8)

        self._status_lbl = QLabel("Enter a search query above.")
        self._status_lbl.setStyleSheet(f"color: {INK_2}; font-size: 13px;")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        results_scroll = QScrollArea()
        results_scroll.setWidgetResizable(True)
        results_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._results_widget = QWidget()
        self._results_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setSpacing(8)
        self._results_layout.setContentsMargins(0, 0, 4, 0)
        self._results_layout.addWidget(self._status_lbl)
        self._results_layout.addStretch()
        results_scroll.setWidget(self._results_widget)
        ro_lay.addWidget(results_scroll)
        body_lay.addWidget(results_outer, stretch=1)

        # Queue panel (330px, collapsible)
        self._queue_panel = QueuePanel()
        self._queue_panel.active_count_changed.connect(self._titlebar.set_active_downloads)
        self._queue_panel.setFixedWidth(330)
        body_lay.addWidget(self._queue_panel)
        shell_layout.addWidget(body, stretch=1)

        # Now Playing Dock
        self._dock = NowPlayingDock(self._player)
        self._dock.download_requested.connect(self._on_download_requested)
        shell_layout.addWidget(self._dock)

        # Resize grip (bottom-right corner, visible on dark theme)
        grip = QSizeGrip(self)
        grip.setFixedSize(18, 18)
        grip.setStyleSheet("background: transparent;")

    def _load_stylesheet(self):
        import os
        qss_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.qss")
        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except OSError:
            pass

    # ── slots ──

    def _set_output_dir(self, path: str):
        self._current_output_dir = path

    def _set_format(self, fmt: str):
        self._current_format = fmt

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._titlebar.refresh_output()
            self._current_output_dir = config.get("output_dir") or ""

    def _toggle_queue(self):
        self._queue_panel.setVisible(not self._queue_panel.isVisible())

    def _on_search(self, query: str, platform: str):
        self._clear_results()
        self._status_lbl.setText("Searching…")
        self._status_lbl.show()

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.terminate()

        self._search_worker = SearchWorker(query, platform)
        self._search_worker.results_ready.connect(self._on_results)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()

    def _on_results(self, results: list):
        self._status_lbl.hide()
        if not results:
            self._status_lbl.setText("No results found.")
            self._status_lbl.show()
            return
        layout = self._results_layout
        stretch_idx = layout.count() - 1
        for r in results:
            card = ResultCard(r)
            card.download_requested.connect(self._on_download_requested)
            card.preview_requested.connect(self._on_preview_requested)
            layout.insertWidget(stretch_idx, card)
            stretch_idx += 1

    def _on_search_error(self, err: str):
        self._status_lbl.setText(f"Search error: {err}")
        self._status_lbl.show()

    def _clear_results(self):
        layout = self._results_layout
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ResultCard):
                w = item.widget()
                layout.removeItem(item)
                w.deleteLater()

    def _on_download_requested(self, result: dict, fmt: str):
        actual_fmt = fmt or self._titlebar.current_format()
        self._queue_panel.enqueue(result, actual_fmt, self._current_output_dir)

    def _on_preview_requested(self, result: dict):
        # Stop any existing preview
        if self._preview_worker and self._preview_worker.isRunning():
            self._preview_worker.terminate()
        self._player.stop()

        # Clear playing state on all cards
        layout = self._results_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.widget(), ResultCard):
                item.widget().set_playing(False)

        self._preview_result = result

        # Mark the card as playing
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, ResultCard) and w.result.get("id") == result.get("id"):
                w.set_playing(True)
                break

        self._dock.set_loading(result)

        self._preview_worker = PreviewWorker(result["url"])
        self._preview_worker.ready.connect(self._on_preview_ready)
        self._preview_worker.duration_ready.connect(self._dock.set_duration)
        self._preview_worker.error.connect(self._on_preview_error)
        self._preview_worker.start()

    def _on_preview_ready(self, path: str):
        self._player.play(path)
        self._dock.set_ready(self._preview_result.get("title", ""))

        # Pass cover to dock
        layout = self._results_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, ResultCard) and w.result.get("id") == self._preview_result.get("id"):
                pix = w.get_cover_pixmap()
                if pix:
                    self._dock.set_cover(pix)
                break

    def _on_preview_error(self, err: str):
        self._dock.hide()
        # Clear playing state
        layout = self._results_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.widget(), ResultCard):
                item.widget().set_playing(False)
        QMessageBox.warning(self, "Preview failed", err)

    def _on_spotify_import(self, url: str):
        worker = SpotifyImportWorker(url)

        dlg = QProgressDialog("Fetching playlist…", "Cancel", 0, 0, self)
        dlg.setWindowTitle("Importing Spotify Playlist")
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setMinimumWidth(360)

        def on_progress(current: int, total: int):
            dlg.setMaximum(total)
            dlg.setValue(current)
            dlg.setLabelText(f"Queuing track {current} of {total}…")

        def on_track(query: str, _display: str):
            sub = SearchWorker(query, "youtube")
            fmt = self._titlebar.current_format()
            out = self._current_output_dir

            def queue_top(results: list):
                if results:
                    self._queue_panel.enqueue(results[0], fmt, out)

            sub.results_ready.connect(queue_top)
            sub.start()

        worker.track_found.connect(on_track)
        worker.progress.connect(on_progress)
        worker.finished.connect(dlg.close)
        worker.error.connect(lambda msg: (dlg.close(), QMessageBox.warning(self, "Spotify Import Error", msg)))
        dlg.canceled.connect(worker.terminate)
        worker.start()
        dlg.exec()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 32, 32)
        p.fillPath(path, QColor(PAPER))

    def closeEvent(self, event):
        self._player.cleanup()
        super().closeEvent(event)
