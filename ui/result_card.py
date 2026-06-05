from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QDialog, QComboBox, QDialogButtonBox,
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QByteArray
import requests
from core.search import format_duration


_PLATFORM_COLORS = {
    "youtube": "#FF0000",
    "soundcloud": "#FF5500",
}


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


class FormatDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download")
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>{title[:60]}</b>"))
        self._combo = QComboBox()
        self._combo.addItems(["MP3 (320kbps)", "FLAC (lossless)"])
        layout.addWidget(self._combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def selected_format(self) -> str:
        return "mp3" if self._combo.currentIndex() == 0 else "flac"


class ResultCard(QWidget):
    download_requested = pyqtSignal(dict, str)   # result dict, format ("mp3"/"flac")
    preview_requested = pyqtSignal(dict)

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result
        self._thumb_loader: ThumbnailLoader | None = None
        self._build()
        self._load_thumbnail()

    def _build(self):
        self.setFixedHeight(72)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 4)
        outer.setSpacing(10)

        self._thumb_label = QLabel()
        self._thumb_label.setFixedSize(64, 64)
        self._thumb_label.setStyleSheet("background: #222; border-radius: 4px;")
        self._thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self._thumb_label)

        info = QVBoxLayout()
        info.setSpacing(2)

        title_font = QFont()
        title_font.setBold(True)
        self._title_lbl = QLabel(self.result["title"])
        self._title_lbl.setFont(title_font)
        self._title_lbl.setMaximumWidth(500)
        self._title_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        info.addWidget(self._title_lbl)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        uploader = self.result.get("uploader", "")
        dur = format_duration(self.result.get("duration", 0))
        meta_lbl = QLabel(f"{uploader}  ·  {dur}")
        meta_lbl.setStyleSheet("color: #888; font-size: 11px;")
        meta_row.addWidget(meta_lbl)

        platform = self.result.get("platform", "")
        color = _PLATFORM_COLORS.get(platform, "#555")
        plat_badge = QLabel(platform.upper())
        plat_badge.setStyleSheet(
            f"background: {color}; color: white; font-size: 10px; "
            "border-radius: 3px; padding: 1px 5px;"
        )
        meta_row.addWidget(plat_badge)
        meta_row.addStretch()
        info.addLayout(meta_row)

        link_lbl = QLabel(f'<a href="{self.result["url"]}">Open in browser</a>')
        link_lbl.setOpenExternalLinks(True)
        link_lbl.setStyleSheet("font-size: 11px;")
        info.addWidget(link_lbl)

        outer.addLayout(info)
        outer.addStretch()

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)

        preview_btn = QPushButton("▶ Preview")
        preview_btn.setFixedWidth(90)
        preview_btn.setStyleSheet(
            "QPushButton { background: #2a2a2a; border: 1px solid #444; "
            "border-radius: 4px; padding: 4px; }"
            "QPushButton:hover { background: #3a3a3a; }"
        )
        preview_btn.clicked.connect(lambda: self.preview_requested.emit(self.result))
        btn_col.addWidget(preview_btn)

        dl_btn = QPushButton("↓ Download")
        dl_btn.setFixedWidth(90)
        dl_btn.setStyleSheet(
            "QPushButton { background: #1a6b1a; border: 1px solid #2a9b2a; "
            "color: white; border-radius: 4px; padding: 4px; }"
            "QPushButton:hover { background: #227722; }"
        )
        dl_btn.clicked.connect(self._on_download)
        btn_col.addWidget(dl_btn)

        outer.addLayout(btn_col)

        self.setStyleSheet(
            "ResultCard { background: #1e1e1e; border-radius: 6px; border: 1px solid #333; }"
        )

    def _load_thumbnail(self):
        thumb_url = self.result.get("thumbnail", "")
        if not thumb_url:
            return
        self._thumb_loader = ThumbnailLoader(thumb_url, self)
        self._thumb_loader.loaded.connect(self._on_thumb_loaded)
        self._thumb_loader.start()

    def _on_thumb_loaded(self, data: QByteArray):
        from PyQt6.QtCore import QRect
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull():
            pix = pix.scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Crop to exactly 64×64 from center
            if pix.width() > 64 or pix.height() > 64:
                x = (pix.width() - 64) // 2
                y = (pix.height() - 64) // 2
                pix = pix.copy(QRect(x, y, 64, 64))
            self._thumb_label.setPixmap(pix)

    def _on_download(self):
        dlg = FormatDialog(self.result["title"], self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.download_requested.emit(self.result, dlg.selected_format())
