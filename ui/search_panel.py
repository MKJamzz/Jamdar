from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
    QPushButton, QLabel, QButtonGroup,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPainter, QPen

INK       = "#221C2B"
INK_2     = "#6E6577"
INK_3     = "#A79FAC"
PAPER     = "#FAF6F2"
LINE      = "#ECE3DC"
SURFACE_2 = "#F0E8E4"
CORAL     = "#FF82A8"
CORAL_DEP = "#E85684"
SP_GREEN  = "#1DB954"


class _PlatformSeg(QWidget):
    """Segmented control with optional colored platform dots."""
    changed = pyqtSignal(int)

    _DOT_COLORS = ["", "#FF3B30", "#FF5500"]  # All / YouTube / SoundCloud
    _LABELS     = ["All", "YouTube", "SoundCloud"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(
            f"_PlatformSeg {{ background: {SURFACE_2}; border-radius: 999px; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(0)
        self._grp = QButtonGroup(self)
        self._grp.setExclusive(True)
        for i, (lbl, dot) in enumerate(zip(self._LABELS, self._DOT_COLORS)):
            text = f"● {lbl}" if dot else lbl
            b = QPushButton(text)
            b.setCheckable(True)
            b.setChecked(i == 0)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self._grp.addButton(b, i)
            lay.addWidget(b)
            self._style_btn(b, i == 0, dot)
        self._grp.idToggled.connect(self._on_toggle)

    def _style_btn(self, btn: QPushButton, active: bool, dot_color: str = ""):
        base_color = dot_color or INK
        if active:
            btn.setStyleSheet(
                "QPushButton { background: white; border: none; border-radius: 999px; "
                f"color: {base_color}; font-size: 12px; font-weight: 600; padding: 3px 12px; }}"
            )
        else:
            btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; border-radius: 999px; "
                f"color: {INK_2}; font-size: 12px; padding: 3px 12px; }}"
                f"QPushButton:hover {{ color: {INK}; }}"
            )

    def _on_toggle(self, btn_id: int, checked: bool):
        if checked:
            for b in self._grp.buttons():
                bid = self._grp.id(b)
                self._style_btn(b, bid == btn_id, self._DOT_COLORS[bid])
            self.changed.emit(btn_id)

    def current_index(self) -> int:
        return self._grp.checkedId()


class SearchPanel(QWidget):
    search_requested  = pyqtSignal(str, str)   # query, platform
    spotify_requested = pyqtSignal(str)         # playlist url

    # kept for back-compat (no longer used internally; format/output live in TitleBar)
    output_dir_changed = pyqtSignal(str)
    format_changed     = pyqtSignal(str)
    settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(16, 12, 12, 8)

        # ── Row 1: search bar ──────────────────────────────────────────────
        search_pill = QWidget()
        search_pill.setFixedHeight(44)
        search_pill.setStyleSheet(
            "QWidget { background: white; border-radius: 999px; "
            f"border: 1.5px solid {LINE}; }}"
        )
        sp_lay = QHBoxLayout(search_pill)
        sp_lay.setContentsMargins(14, 0, 6, 0)
        sp_lay.setSpacing(8)

        # magnifier icon
        mag = QLabel("🔍")
        mag.setStyleSheet(f"font-size: 14px; color: {INK_3}; background: transparent; border: none;")
        sp_lay.addWidget(mag)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search for music…")
        self._search_edit.setStyleSheet(
            f"QLineEdit {{ border: none; background: transparent; color: {INK}; "
            f"font-size: 14px; padding: 0; }}"
        )
        self._search_edit.returnPressed.connect(self._on_search)
        sp_lay.addWidget(self._search_edit, stretch=1)

        self._platform_seg = _PlatformSeg()
        self._platform_seg.changed.connect(lambda _: None)  # optional hook
        sp_lay.addWidget(self._platform_seg)

        search_btn = QPushButton("Search")
        search_btn.setFixedHeight(34)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setStyleSheet(
            f"QPushButton {{ background: {CORAL}; border: none; border-radius: 999px; "
            f"color: white; font-size: 13px; font-weight: 600; padding: 0 18px; "
            f"border: none; }}"
            f"QPushButton:hover {{ background: {CORAL_DEP}; }}"
        )
        search_btn.clicked.connect(self._on_search)
        sp_lay.addWidget(search_btn)

        root.addWidget(search_pill)

        # ── Row 2: Spotify import ──────────────────────────────────────────
        sp_row = QHBoxLayout()
        sp_row.setSpacing(8)
        sp_row.setContentsMargins(4, 0, 0, 0)

        sp_badge = QLabel("♪")
        sp_badge.setFixedSize(22, 22)
        sp_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sp_badge.setStyleSheet(
            f"background: {SP_GREEN}; color: white; border-radius: 11px; "
            "font-size: 12px; font-weight: 700;"
        )
        sp_row.addWidget(sp_badge)

        self._sp_edit = QLineEdit()
        self._sp_edit.setPlaceholderText("Paste Spotify playlist URL to bulk-download…")
        self._sp_edit.setFixedHeight(32)
        self._sp_edit.setStyleSheet(
            f"QLineEdit {{ background: {SURFACE_2}; border: 1px solid {LINE}; border-radius: 999px; "
            f"color: {INK}; padding: 0 12px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border-color: {SP_GREEN}; }}"
        )
        sp_row.addWidget(self._sp_edit, stretch=1)

        import_btn = QPushButton("Import")
        import_btn.setFixedHeight(32)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setStyleSheet(
            f"QPushButton {{ background: {SP_GREEN}; border: none; border-radius: 999px; "
            f"color: white; font-size: 12px; font-weight: 600; padding: 0 14px; }}"
            f"QPushButton:hover {{ background: #17a349; }}"
        )
        import_btn.clicked.connect(self._on_spotify)
        sp_row.addWidget(import_btn)

        hint = QLabel("Press Enter or click Search")
        hint.setStyleSheet(f"color: {INK_3}; font-size: 11px; background: transparent;")
        sp_row.addWidget(hint)

        root.addLayout(sp_row)

    def _on_search(self):
        query = self._search_edit.text().strip()
        if not query:
            return
        platform = ["both", "youtube", "soundcloud"][self._platform_seg.current_index()]
        self.search_requested.emit(query, platform)

    def _on_spotify(self):
        url = self._sp_edit.text().strip()
        if url:
            self.spotify_requested.emit(url)

    # kept for compatibility (called by old settings refresh flow)
    def refresh_output_display(self):
        pass

    def current_format(self) -> str:
        import config as _cfg
        return _cfg.get("default_format") or "mp3"

    def current_output_dir(self) -> str:
        import config as _cfg
        return _cfg.get("output_dir") or ""
