import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QDialogButtonBox,
)
import config


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        # Output directory
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit(config.get("output_dir"))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self._dir_edit)
        dir_row.addWidget(browse_btn)
        form.addRow("Default output folder:", dir_row)

        # Spotify credentials
        sp_label = QLabel(
            "<b>Spotify credentials</b> (needed for playlist import)<br>"
            "Get free credentials at <a href='https://developer.spotify.com/dashboard'>"
            "developer.spotify.com/dashboard</a>"
        )
        sp_label.setOpenExternalLinks(True)
        sp_label.setWordWrap(True)
        layout.addLayout(form)
        layout.addWidget(sp_label)

        sp_form = QFormLayout()
        sp_form.setSpacing(8)
        self._client_id = QLineEdit(config.get("spotify_client_id"))
        self._client_id.setPlaceholderText("Client ID")
        self._client_secret = QLineEdit(config.get("spotify_client_secret"))
        self._client_secret.setPlaceholderText("Client Secret")
        self._client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        sp_form.addRow("Client ID:", self._client_id)
        sp_form.addRow("Client Secret:", self._client_secret)
        layout.addLayout(sp_form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select output folder", self._dir_edit.text())
        if path:
            self._dir_edit.setText(path)

    def _save(self):
        config.set("output_dir", self._dir_edit.text())
        config.set("spotify_client_id", self._client_id.text().strip())
        config.set("spotify_client_secret", self._client_secret.text().strip())
        self.accept()
