from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QDialogButtonBox,
    QWidget,
)
from PyQt6.QtCore import Qt
import config

INK        = "#221C2B"
INK_2      = "#6E6577"
PAPER      = "#FAF6F2"
SURFACE_2  = "#F0E8E4"
LINE       = "#ECE3DC"
CORAL      = "#FF82A8"
CORAL_DEEP = "#E85684"


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self._build()
        self._apply_style()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(
            f"font-family: 'Bricolage Grotesque 96pt ExtraBold', sans-serif; font-size: 20px; "
            f"font-weight: 700; color: {INK};"
        )
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit(config.get("output_dir"))
        self._dir_edit.setPlaceholderText("Output folder path…")
        browse_btn = QPushButton("Browse…")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setFixedHeight(34)
        browse_btn.setStyleSheet(
            f"QPushButton {{ background: {SURFACE_2}; border: none; border-radius: 8px; "
            f"color: {INK}; padding: 0 12px; }}"
            f"QPushButton:hover {{ background: {LINE}; }}"
        )
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self._dir_edit)
        dir_row.addWidget(browse_btn)
        form.addRow("Default output folder:", dir_row)
        layout.addLayout(form)

        # Spotify section
        sp_label = QLabel(
            "<b>Spotify credentials</b> (needed for playlist import)<br>"
            "Get free credentials at <a href='https://developer.spotify.com/dashboard'>"
            "developer.spotify.com/dashboard</a>"
        )
        sp_label.setOpenExternalLinks(True)
        sp_label.setWordWrap(True)
        sp_label.setStyleSheet(f"color: {INK_2}; font-size: 12px;")
        layout.addWidget(sp_label)

        sp_form = QFormLayout()
        sp_form.setSpacing(8)
        sp_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self._client_id = QLineEdit(config.get("spotify_client_id"))
        self._client_id.setPlaceholderText("Client ID")
        sp_form.addRow("Client ID:", self._client_id)

        self._client_secret = QLineEdit(config.get("spotify_client_secret"))
        self._client_secret.setPlaceholderText("Client Secret")
        self._client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        sp_form.addRow("Client Secret:", self._client_secret)
        layout.addLayout(sp_form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {PAPER};
                color: {INK};
                font-family: 'Hanken Grotesk', 'Segoe UI', sans-serif;
                font-size: 13px;
            }}
            QLabel {{ color: {INK}; background: transparent; }}
            QLineEdit {{
                background: white;
                border: 1.5px solid {LINE};
                border-radius: 10px;
                padding: 6px 12px;
                color: {INK};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {CORAL}; }}
            QDialogButtonBox QPushButton {{
                min-width: 70px;
                height: 34px;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 16px;
                border: none;
            }}
            QDialogButtonBox QPushButton[text="OK"] {{
                background: {CORAL};
                color: white;
            }}
            QDialogButtonBox QPushButton[text="OK"]:hover {{
                background: {CORAL_DEEP};
            }}
            QDialogButtonBox QPushButton:not([text="OK"]) {{
                background: {SURFACE_2};
                color: {INK};
            }}
            QDialogButtonBox QPushButton:not([text="OK"]):hover {{
                background: {LINE};
            }}
        """)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select output folder", self._dir_edit.text())
        if path:
            self._dir_edit.setText(path)

    def _save(self):
        config.set("output_dir", self._dir_edit.text())
        config.set("spotify_client_id", self._client_id.text().strip())
        config.set("spotify_client_secret", self._client_secret.text().strip())
        self.accept()
