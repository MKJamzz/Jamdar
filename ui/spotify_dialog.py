from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox,
)
from PyQt6.QtCore import Qt

INK       = "#221C2B"
INK_2     = "#6E6577"
INK_3     = "#A79FAC"
PAPER     = "#FAF6F2"
LINE      = "#ECE3DC"
SURFACE_2 = "#F0E8E4"
SP_GREEN  = "#1DB954"


class SpotifyPlaylistDialog(QDialog):
    def __init__(self, playlist_name: str, tracks: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Spotify Playlist")
        self.resize(640, 580)
        self.setMinimumWidth(540)
        self._tracks = tracks
        self._checks: list[QCheckBox] = []
        self._build(playlist_name)

    def _build(self, playlist_name: str):
        self.setStyleSheet(f"QDialog {{ background: {PAPER}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background: white; border-bottom: 1px solid {LINE};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)
        h_lay.setSpacing(16)

        badge = QLabel("♪")
        badge.setFixedSize(44, 44)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background: {SP_GREEN}; color: white; border-radius: 22px; "
            "font-size: 20px; font-weight: 700;"
        )
        h_lay.addWidget(badge)

        tc = QVBoxLayout()
        tc.setSpacing(3)

        name_lbl = QLabel(playlist_name)
        name_lbl.setStyleSheet(
            f"font-size: 17px; font-weight: 700; color: {INK}; background: transparent;"
        )
        tc.addWidget(name_lbl)

        sub_lbl = QLabel(f"{len(self._tracks)} tracks · Spotify Playlist")
        sub_lbl.setStyleSheet(
            f"font-size: 12px; color: {INK_2}; background: transparent;"
        )
        tc.addWidget(sub_lbl)
        h_lay.addLayout(tc, stretch=1)

        root.addWidget(header)

        # ── Select-all bar ────────────────────────────────────────────────────
        bar = QWidget()
        bar.setFixedHeight(42)
        bar.setStyleSheet(f"background: {SURFACE_2}; border-bottom: 1px solid {LINE};")
        b_lay = QHBoxLayout(bar)
        b_lay.setContentsMargins(24, 0, 24, 0)

        self._all_cb = QCheckBox("Select all")
        self._all_cb.setTristate(True)
        self._all_cb.setCheckState(Qt.CheckState.Checked)
        self._all_cb.setStyleSheet(
            f"QCheckBox {{ font-size: 12px; font-weight: 600; color: {INK}; background: transparent; }}"
            + _cb_indicator_style()
        )
        self._all_cb.clicked.connect(self._on_select_all_clicked)
        b_lay.addWidget(self._all_cb)
        b_lay.addStretch()

        self._sel_lbl = QLabel(f"{len(self._tracks)} selected")
        self._sel_lbl.setStyleSheet(
            f"font-size: 11px; color: {INK_2}; background: transparent;"
        )
        b_lay.addWidget(self._sel_lbl)
        root.addWidget(bar)

        # ── Track list ────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet(f"background: {PAPER};")
        list_lay = QVBoxLayout(inner)
        list_lay.setContentsMargins(12, 8, 12, 8)
        list_lay.setSpacing(1)

        for idx, (name, artists) in enumerate(self._tracks):
            row = _TrackRow(idx + 1, name, artists)
            cb = row.checkbox()
            cb.stateChanged.connect(self._update_count)
            self._checks.append(cb)
            list_lay.addWidget(row)

        list_lay.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, stretch=1)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setFixedHeight(64)
        footer.setStyleSheet(f"background: white; border-top: 1px solid {LINE};")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(24, 0, 24, 0)
        f_lay.setSpacing(10)
        f_lay.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(38)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(
            f"QPushButton {{ background: {SURFACE_2}; border: none; border-radius: 999px; "
            f"color: {INK}; font-size: 13px; padding: 0 22px; }}"
            f"QPushButton:hover {{ background: {LINE}; }}"
        )
        cancel.clicked.connect(self.reject)
        f_lay.addWidget(cancel)

        self._dl_btn = QPushButton(f"Download {len(self._tracks)} tracks  →")
        self._dl_btn.setFixedHeight(38)
        self._dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dl_btn.setStyleSheet(
            f"QPushButton {{ background: {SP_GREEN}; border: none; border-radius: 999px; "
            f"color: white; font-size: 13px; font-weight: 600; padding: 0 22px; }}"
            "QPushButton:hover { background: #17a349; }"
            "QPushButton:disabled { background: #cccccc; color: #999; }"
        )
        self._dl_btn.clicked.connect(self.accept)
        f_lay.addWidget(self._dl_btn)

        root.addWidget(footer)

    def _on_select_all_clicked(self):
        n = sum(1 for cb in self._checks if cb.isChecked())
        check_all = n < len(self._checks)
        for cb in self._checks:
            cb.blockSignals(True)
            cb.setChecked(check_all)
            cb.blockSignals(False)
        self._update_count()

    def _update_count(self):
        n = sum(1 for cb in self._checks if cb.isChecked())
        self._sel_lbl.setText(f"{n} selected")
        self._dl_btn.setEnabled(n > 0)
        self._dl_btn.setText(
            f"Download {n} track{'s' if n != 1 else ''}  →" if n > 0 else "No tracks selected"
        )

        self._all_cb.blockSignals(True)
        if n == 0:
            self._all_cb.setCheckState(Qt.CheckState.Unchecked)
        elif n == len(self._checks):
            self._all_cb.setCheckState(Qt.CheckState.Checked)
        else:
            self._all_cb.setCheckState(Qt.CheckState.PartiallyChecked)
        self._all_cb.blockSignals(False)

    def selected_tracks(self) -> list[tuple[str, str]]:
        return [t for t, cb in zip(self._tracks, self._checks) if cb.isChecked()]


class _TrackRow(QWidget):
    def __init__(self, num: int, name: str, artists: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(
            "QWidget { background: transparent; border-radius: 8px; }"
            f"QWidget:hover {{ background: {SURFACE_2}; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(12)

        self._cb = QCheckBox()
        self._cb.setChecked(True)
        self._cb.setStyleSheet(_cb_indicator_style())
        lay.addWidget(self._cb)

        num_lbl = QLabel(f"{num:02d}")
        num_lbl.setFixedWidth(26)
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        num_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono', monospace; font-size: 11px; "
            f"color: {INK_3}; background: transparent;"
        )
        lay.addWidget(num_lbl)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {INK}; background: transparent;"
        )
        lay.addWidget(name_lbl, stretch=3)

        artist_lbl = QLabel(artists)
        artist_lbl.setStyleSheet(
            f"font-size: 12px; color: {INK_2}; background: transparent;"
        )
        lay.addWidget(artist_lbl, stretch=2)

    def checkbox(self) -> QCheckBox:
        return self._cb


def _cb_indicator_style() -> str:
    return (
        f"QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; "
        f"border: 1.5px solid {INK_3}; background: white; }}"
        f"QCheckBox::indicator:checked {{ background: {SP_GREEN}; border-color: {SP_GREEN}; }}"
        f"QCheckBox::indicator:indeterminate {{ background: {SP_GREEN}; border-color: {SP_GREEN}; }}"
    )
