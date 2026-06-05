import math

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QByteArray, QTimer, QRect
import requests
from core.search import format_duration

# ── colour tokens (matches main_window.py) ────────────────────────────────────
INK        = "#221C2B"
INK_2      = "#6E6577"
INK_3      = "#A79FAC"
SURFACE    = "#FFFFFF"
LINE       = "#ECE3DC"
CORAL      = "#FF82A8"
CORAL_DEEP = "#E85684"
CORAL_SOFT = "#FFE6EE"
SURFACE_2  = "#F0E8E4"

_PLATFORM_COLORS = {
    "youtube":    "#FF3B30",
    "soundcloud": "#FF5500",
}


# ══════════════════════════════════════════════════════════════════════════════
#  ThumbnailLoader
# ══════════════════════════════════════════════════════════════════════════════

class ThumbnailLoader(QThread):
    loaded = pyqtSignal(QByteArray)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            r = requests.get(self.url, timeout=5)
            if r.ok:
                self.loaded.emit(QByteArray(r.content))
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  EqualizerWidget — 4 animated coral bars
# ══════════════════════════════════════════════════════════════════════════════

class EqualizerWidget(QWidget):
    _PHASES = [0.0, 1.8, 0.6, 2.8]   # staggered start phases

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 14)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._step)
        self._active = False

    def start(self):
        self._active = True
        self._timer.start()

    def stop(self):
        self._active = False
        self._timer.stop()
        self.update()

    def _step(self):
        self._t += 0.18
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bar_w, gap = 3, 2
        for i in range(4):
            if self._active:
                h = int(4 + 9 * (0.5 + 0.5 * math.sin(self._t + self._PHASES[i])))
            else:
                h = 4
            x = i * (bar_w + gap)
            y = (self.height() - h) // 2
            p.setBrush(QColor(CORAL))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x, y, bar_w, h, 1.5, 1.5)


# ══════════════════════════════════════════════════════════════════════════════
#  ResultCard
# ══════════════════════════════════════════════════════════════════════════════

class ResultCard(QWidget):
    download_requested = pyqtSignal(dict, str)  # result, format
    preview_requested  = pyqtSignal(dict)

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result
        self._playing = False
        self._pixmap: QPixmap | None = None
        self._thumb_loader: ThumbnailLoader | None = None
        self._build()
        self._load_thumbnail()

    # ── build ──────────────────────────────────────────────────────────────

    def _build(self):
        self.setMinimumHeight(96)
        self.setMaximumHeight(100)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._apply_style(playing=False)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(14)

        # Cover container (80×80 + platform badge overlay)
        cover_container = QWidget()
        cover_container.setFixedSize(80, 80)
        cover_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._thumb_lbl = QLabel(cover_container)
        self._thumb_lbl.setGeometry(0, 0, 80, 80)
        self._thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_lbl.setStyleSheet(
            "border-radius: 15px; background: qlineargradient("
            "x1:0,y1:0,x2:1,y2:1,stop:0 #E8D8F0,stop:1 #D0C0E8);"
        )

        # Platform badge (bottom-left of cover)
        platform = self.result.get("platform", "")
        plat_color = _PLATFORM_COLORS.get(platform, "#555")
        plat_short = "YT" if platform == "youtube" else "SC" if platform == "soundcloud" else platform.upper()[:2]
        self._plat_badge = QLabel(plat_short, cover_container)
        self._plat_badge.setGeometry(4, 56, 28, 20)
        self._plat_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._plat_badge.setStyleSheet(
            f"background: {plat_color}; color: white; border-radius: 6px; "
            "font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: 700;"
        )

        self._coral_ring = QWidget(cover_container)
        self._coral_ring.setGeometry(-2, -2, 84, 84)
        self._coral_ring.setStyleSheet(
            f"border: 3px solid {CORAL}; border-radius: 17px; background: transparent;"
        )
        self._coral_ring.hide()

        outer.addWidget(cover_container)

        # Meta column
        meta = QVBoxLayout()
        meta.setSpacing(4)
        meta.setContentsMargins(0, 0, 0, 0)

        self._title_lbl = QLabel(self.result.get("title", ""))
        self._title_lbl.setStyleSheet(
            f"font-family: 'Bricolage Grotesque 96pt ExtraBold', sans-serif; font-size: 15px; "
            f"font-weight: 700; color: {INK}; background: transparent;"
        )
        self._title_lbl.setMaximumWidth(600)
        self._title_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        meta.addWidget(self._title_lbl)

        # Sub-line: [equalizer] [platform dot] uploader · duration
        sub_row = QHBoxLayout()
        sub_row.setSpacing(6)
        sub_row.setContentsMargins(0, 0, 0, 0)

        self._eq = EqualizerWidget()
        self._eq.hide()
        sub_row.addWidget(self._eq)

        self._now_lbl = QLabel("Now previewing")
        self._now_lbl.setStyleSheet(
            f"color: {CORAL_DEEP}; font-size: 12px; font-style: italic; background: transparent;"
        )
        self._now_lbl.hide()
        sub_row.addWidget(self._now_lbl)

        platform_dot = QLabel("●")
        platform_dot.setStyleSheet(
            f"color: {plat_color}; font-size: 9px; background: transparent;"
        )
        sub_row.addWidget(platform_dot)

        uploader = self.result.get("uploader", "")
        dur = format_duration(self.result.get("duration", 0))
        self._meta_lbl = QLabel(f"{uploader}  ·  {dur}")
        self._meta_lbl.setStyleSheet(
            f"color: {INK_2}; font-size: 12.5px; background: transparent;"
        )
        sub_row.addWidget(self._meta_lbl)
        sub_row.addStretch()

        meta.addLayout(sub_row)
        meta.addStretch()
        outer.addLayout(meta, stretch=1)

        # Action buttons
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)
        btn_col.setContentsMargins(0, 0, 0, 0)

        self._preview_btn = QPushButton("▶  Preview")
        self._preview_btn.setFixedWidth(100)
        self._preview_btn.setFixedHeight(32)
        self._preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._preview_btn.setStyleSheet(self._preview_style(playing=False))
        self._preview_btn.clicked.connect(self._on_preview_click)
        btn_col.addWidget(self._preview_btn)

        dl_btn = QPushButton("↓  Download")
        dl_btn.setFixedWidth(100)
        dl_btn.setFixedHeight(32)
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.setStyleSheet(
            f"QPushButton {{ background: {CORAL}; border: none; border-radius: 999px; "
            f"color: white; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {CORAL_DEEP}; }}"
        )
        dl_btn.clicked.connect(self._on_download)
        btn_col.addWidget(dl_btn)

        outer.addLayout(btn_col)

    # ── public API ──────────────────────────────────────────────────────────

    def set_playing(self, playing: bool):
        self._playing = playing
        self._apply_style(playing)
        self._coral_ring.setVisible(playing)
        self._eq.setVisible(playing)
        self._now_lbl.setVisible(playing)
        self._preview_btn.setText("⏸  Pause" if playing else "▶  Preview")
        self._preview_btn.setStyleSheet(self._preview_style(playing))
        if playing:
            self._eq.start()
        else:
            self._eq.stop()

    def get_cover_pixmap(self) -> QPixmap | None:
        return self._pixmap

    # ── internals ──────────────────────────────────────────────────────────

    def _apply_style(self, playing: bool):
        border = f"2px solid {CORAL}" if playing else f"1px solid {LINE}"
        self.setStyleSheet(
            f"ResultCard {{ background: {SURFACE}; border-radius: 20px; border: {border}; }}"
            f"ResultCard:hover {{ border: {'2px solid ' + CORAL if playing else '1px solid #D5C8C0'}; }}"
        )

    @staticmethod
    def _preview_style(playing: bool) -> str:
        if playing:
            return (
                f"QPushButton {{ background: {CORAL_SOFT}; border: 1.5px solid {CORAL}; "
                f"border-radius: 999px; color: {CORAL_DEEP}; font-size: 12px; font-weight: 600; }}"
                f"QPushButton:hover {{ background: {CORAL}; color: white; }}"
            )
        return (
            "QPushButton { background: transparent; border: 1.5px solid #D5C8C0; "
            f"border-radius: 999px; color: {INK_2}; font-size: 12px; }}"
            f"QPushButton:hover {{ border-color: {CORAL}; color: {CORAL_DEEP}; }}"
        )

    def _on_preview_click(self):
        self.preview_requested.emit(self.result)

    def _on_download(self):
        import config as _cfg
        fmt = _cfg.get("default_format") or "mp3"
        self.download_requested.emit(self.result, fmt)

    def _load_thumbnail(self):
        url = self.result.get("thumbnail", "")
        if not url:
            return
        self._thumb_loader = ThumbnailLoader(url, self)
        self._thumb_loader.loaded.connect(self._on_thumb)
        self._thumb_loader.start()

    def _on_thumb(self, data: QByteArray):
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull():
            pix = pix.scaled(
                80, 80,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            if pix.width() > 80 or pix.height() > 80:
                x = (pix.width() - 80) // 2
                y = (pix.height() - 80) // 2
                pix = pix.copy(QRect(x, y, 80, 80))
            self._pixmap = pix
            self._thumb_lbl.setPixmap(pix)
            self._thumb_lbl.setStyleSheet(
                "border-radius: 15px; background: transparent;"
            )
