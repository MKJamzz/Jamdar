import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QFileDialog,
)
from PyQt6.QtCore import pyqtSignal
import config


class SearchPanel(QWidget):
    search_requested = pyqtSignal(str, str)       # query, platform
    spotify_requested = pyqtSignal(str)           # playlist url
    output_dir_changed = pyqtSignal(str)
    format_changed = pyqtSignal(str)
    settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Row 1: search bar + platform dropdown + search button
        row1 = QHBoxLayout()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search for music…")
        self._search_edit.setMinimumHeight(36)
        self._search_edit.returnPressed.connect(self._on_search)
        row1.addWidget(self._search_edit)

        row1.addWidget(QLabel("Search on:"))
        self._platform_combo = QComboBox()
        self._platform_combo.addItems([
            "YouTube + SoundCloud",
            "YouTube only",
            "SoundCloud only",
        ])
        self._platform_combo.setMinimumHeight(36)
        self._platform_combo.setMinimumWidth(180)
        row1.addWidget(self._platform_combo)

        search_btn = QPushButton("Search")
        search_btn.setMinimumHeight(36)
        search_btn.setMinimumWidth(80)
        search_btn.setStyleSheet(
            "QPushButton { background: #2196F3; color: white; border-radius: 4px; "
            "font-weight: bold; padding: 0 12px; }"
            "QPushButton:hover { background: #1976D2; }"
        )
        search_btn.clicked.connect(self._on_search)
        row1.addWidget(search_btn)
        layout.addLayout(row1)

        # Row 2: Spotify import
        row2 = QHBoxLayout()
        self._sp_edit = QLineEdit()
        self._sp_edit.setPlaceholderText("Paste Spotify playlist URL to bulk-download…")
        self._sp_edit.setMinimumHeight(32)
        row2.addWidget(self._sp_edit)
        import_btn = QPushButton("Import Playlist")
        import_btn.setMinimumHeight(32)
        import_btn.setStyleSheet(
            "QPushButton { background: #1DB954; color: white; border-radius: 4px; "
            "padding: 0 12px; }"
            "QPushButton:hover { background: #17a349; }"
        )
        import_btn.clicked.connect(self._on_spotify)
        row2.addWidget(import_btn)
        layout.addLayout(row2)

        # Row 3: output path display + format + settings
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Output:"))

        self._out_label = QLineEdit(config.get("output_dir"))
        self._out_label.setReadOnly(True)
        self._out_label.setMinimumWidth(220)
        self._out_label.setStyleSheet(
            "QLineEdit { color: #aaa; background: #1a1a1a; border-color: #2a2a2a; }"
        )
        row3.addWidget(self._out_label, stretch=1)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(32)
        browse_btn.setToolTip("Browse for output folder")
        browse_btn.clicked.connect(self._browse_dir)
        row3.addWidget(browse_btn)

        row3.addSpacing(12)
        row3.addWidget(QLabel("Format:"))
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["MP3 (320kbps)", "FLAC (lossless)"])
        saved_fmt = config.get("default_format")
        self._fmt_combo.setCurrentIndex(0 if saved_fmt == "mp3" else 1)
        self._fmt_combo.currentIndexChanged.connect(self._on_format_changed)
        row3.addWidget(self._fmt_combo)

        row3.addStretch()
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self.settings_requested.emit)
        row3.addWidget(settings_btn)
        layout.addLayout(row3)

    def _on_search(self):
        query = self._search_edit.text().strip()
        if not query:
            return
        platform = ["both", "youtube", "soundcloud"][self._platform_combo.currentIndex()]
        self.search_requested.emit(query, platform)

    def _on_spotify(self):
        url = self._sp_edit.text().strip()
        if url:
            self.spotify_requested.emit(url)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select output folder", config.get("output_dir"))
        if path:
            config.set("output_dir", path)
            self._out_label.setText(path)
            self.output_dir_changed.emit(path)

    def refresh_output_display(self):
        path = config.get("output_dir")
        self._out_label.setText(path)
        self.output_dir_changed.emit(path)

    def _on_format_changed(self, idx: int):
        fmt = "mp3" if idx == 0 else "flac"
        config.set("default_format", fmt)
        self.format_changed.emit(fmt)

    def current_format(self) -> str:
        return "mp3" if self._fmt_combo.currentIndex() == 0 else "flac"

    def current_output_dir(self) -> str:
        return config.get("output_dir")
