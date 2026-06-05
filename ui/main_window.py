from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QSplitter, QMessageBox, QProgressDialog, QPushButton, QSlider,
    QDialog,
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal

from ui.search_panel import SearchPanel
from ui.result_card import ResultCard
from ui.queue_panel import QueuePanel
from ui.settings_dialog import SettingsDialog
from core.search import SearchWorker
from core.preview import PreviewWorker, Player
from core.spotify import SpotifyImportWorker
import config


def _fmt_time(ms: int) -> str:
    s = max(0, ms // 1000)
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"


class MiniPlayerBar(QWidget):
    def __init__(self, player: Player, parent=None):
        super().__init__(parent)
        self._player = player
        self._duration_ms = 30_000
        self._dragging = False
        self._paused = False
        self._build()

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._tick)

        self.hide()

    def _build(self):
        self.setFixedHeight(52)
        self.setStyleSheet(
            "MiniPlayerBar { background: #1a2a3a; border: 1px solid #2a4a6a; border-radius: 6px; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        self._play_btn = QPushButton("⏸")
        self._play_btn.setFixedSize(32, 32)
        self._play_btn.setStyleSheet(
            "QPushButton { background: #2196F3; border: none; border-radius: 16px; "
            "color: white; font-size: 14px; }"
            "QPushButton:hover { background: #1976D2; }"
        )
        self._play_btn.clicked.connect(self._toggle_pause)
        layout.addWidget(self._play_btn)

        self._title_lbl = QLabel("Loading preview…")
        self._title_lbl.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        self._title_lbl.setMaximumWidth(260)
        layout.addWidget(self._title_lbl)

        self._time_lbl = QLabel("0:00 / 0:30")
        self._time_lbl.setStyleSheet("color: #aaa; font-size: 11px; min-width: 80px;")
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._time_lbl)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 1000)
        self._slider.setValue(0)
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px; background: #2a4a6a; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px; height: 14px; margin: -5px 0;
                background: #2196F3; border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #2196F3; border-radius: 2px;
            }
        """)
        self._slider.sliderPressed.connect(self._on_drag_start)
        self._slider.sliderReleased.connect(self._on_drag_end)
        layout.addWidget(self._slider, stretch=1)

        stop_btn = QPushButton("✕")
        stop_btn.setFixedSize(24, 24)
        stop_btn.setToolTip("Stop preview")
        stop_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #666; font-size: 14px; }"
            "QPushButton:hover { color: #cc4444; }"
        )
        stop_btn.clicked.connect(self._stop)
        layout.addWidget(stop_btn)

    def set_loading(self, title: str):
        self._title_lbl.setText(f"{title[:40]}…" if len(title) > 40 else title)
        self._play_btn.setText("…")
        self._play_btn.setEnabled(False)
        self._slider.setValue(0)
        self._time_lbl.setText("Loading…")
        self.show()

    def set_duration(self, seconds: float):
        self._duration_ms = int(seconds * 1000)
        self._time_lbl.setText(f"0:00 / {_fmt_time(self._duration_ms)}")

    def on_ready(self, title: str):
        self._title_lbl.setText(f"{title[:40]}…" if len(title) > 40 else title)
        self._play_btn.setText("⏸")
        self._play_btn.setEnabled(True)
        self._paused = False
        self._timer.start()

    def _tick(self):
        pos_ms = self._player.get_position_ms()
        if not self._dragging:
            if self._duration_ms > 0:
                self._slider.setValue(int(pos_ms / self._duration_ms * 1000))
            self._time_lbl.setText(f"{_fmt_time(pos_ms)} / {_fmt_time(self._duration_ms)}")

        # Auto-hide when playback finishes naturally
        if pos_ms >= 0 and not self._player.is_playing() and not self._player.is_paused():
            self._stop()

    def _toggle_pause(self):
        if self._paused:
            self._player.resume()
            self._play_btn.setText("⏸")
            self._paused = False
        else:
            self._player.pause()
            self._play_btn.setText("▶")
            self._paused = True

    def _on_drag_start(self):
        self._dragging = True

    def _on_drag_end(self):
        self._dragging = False
        frac = self._slider.value() / 1000.0
        target_s = frac * self._duration_ms / 1000.0
        self._player.set_position(target_s)

    def _stop(self):
        self._timer.stop()
        self._player.stop()
        self.hide()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jamdar")
        self.setMinimumSize(QSize(800, 640))
        self._search_worker: SearchWorker | None = None
        self._preview_worker: PreviewWorker | None = None
        self._preview_title = ""
        self._player = Player()
        self._current_output_dir = config.get("output_dir")
        self._current_format = config.get("default_format")
        self._build()
        self._apply_theme()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 8)
        root.setSpacing(8)

        self._search_panel = SearchPanel()
        self._search_panel.search_requested.connect(self._on_search)
        self._search_panel.spotify_requested.connect(self._on_spotify_import)
        self._search_panel.output_dir_changed.connect(self._set_output_dir)
        self._search_panel.format_changed.connect(self._set_format)
        self._search_panel.settings_requested.connect(self._open_settings)
        root.addWidget(self._search_panel)

        self._mini_player = MiniPlayerBar(self._player)
        root.addWidget(self._mini_player)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results area
        results_container = QWidget()
        rc_layout = QVBoxLayout(results_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.setSpacing(4)

        res_header = QLabel("RESULTS")
        res_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;")
        rc_layout.addWidget(res_header)

        self._status_lbl = QLabel("Enter a search query above.")
        self._status_lbl.setStyleSheet("color: #555; font-size: 12px;")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        results_scroll = QScrollArea()
        results_scroll.setWidgetResizable(True)
        results_scroll.setStyleSheet("QScrollArea { border: none; }")
        self._results_widget = QWidget()
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setSpacing(6)
        self._results_layout.setContentsMargins(0, 0, 4, 0)
        self._results_layout.addWidget(self._status_lbl)
        self._results_layout.addStretch()
        results_scroll.setWidget(self._results_widget)
        rc_layout.addWidget(results_scroll)

        splitter.addWidget(results_container)

        self._queue_panel = QueuePanel()
        splitter.addWidget(self._queue_panel)

        splitter.setSizes([420, 200])
        root.addWidget(splitter)

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #121212;
                color: #e0e0e0;
                font-family: "Segoe UI", "Noto Sans", sans-serif;
                font-size: 13px;
            }
            QLineEdit {
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
            }
            QLineEdit:focus { border-color: #2196F3; }
            QComboBox {
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1e1e1e;
                border: 1px solid #444;
                selection-background-color: #2196F3;
            }
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 10px;
                color: #e0e0e0;
            }
            QPushButton:hover { background: #333; }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #333;
                border-radius: 4px;
                min-height: 20px;
            }
            QSplitter::handle { background: #2a2a2a; height: 3px; }
        """)

    # --- slots ---

    def _set_output_dir(self, path: str):
        self._current_output_dir = path

    def _set_format(self, fmt: str):
        self._current_format = fmt

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._search_panel.refresh_output_display()
            self._current_output_dir = config.get("output_dir")

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
                item.widget().deleteLater()
                layout.removeItem(item)

    def _on_download_requested(self, result: dict, fmt: str):
        self._queue_panel.enqueue(result, fmt, self._current_output_dir)

    def _on_preview_requested(self, result: dict):
        if self._preview_worker and self._preview_worker.isRunning():
            self._preview_worker.terminate()

        self._player.stop()
        self._preview_title = result.get("title", "Unknown")
        self._mini_player.set_loading(self._preview_title)

        self._preview_worker = PreviewWorker(result["url"])
        self._preview_worker.ready.connect(self._on_preview_ready)
        self._preview_worker.duration_ready.connect(self._mini_player.set_duration)
        self._preview_worker.error.connect(self._on_preview_error)
        self._preview_worker.start()

    def _on_preview_ready(self, path: str):
        self._player.play(path)
        self._mini_player.on_ready(self._preview_title)

    def _on_preview_error(self, err: str):
        self._mini_player.hide()
        QMessageBox.warning(self, "Preview failed", err)

    def _on_spotify_import(self, url: str):
        worker = SpotifyImportWorker(url)

        progress_dlg = QProgressDialog("Fetching playlist…", "Cancel", 0, 0, self)
        progress_dlg.setWindowTitle("Importing Spotify Playlist")
        progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dlg.setMinimumWidth(360)

        def on_progress(current: int, total: int):
            progress_dlg.setMaximum(total)
            progress_dlg.setValue(current)
            progress_dlg.setLabelText(f"Queuing track {current} of {total}…")

        def on_track(query: str, display: str):
            sub = SearchWorker(query, "youtube")
            fmt = self._search_panel.current_format()
            out = self._current_output_dir

            def queue_top(results: list):
                if results:
                    self._queue_panel.enqueue(results[0], fmt, out)

            sub.results_ready.connect(queue_top)
            sub.start()

        def on_done():
            progress_dlg.close()

        def on_error(msg: str):
            progress_dlg.close()
            QMessageBox.warning(self, "Spotify Import Error", msg)

        worker.track_found.connect(on_track)
        worker.progress.connect(on_progress)
        worker.finished.connect(on_done)
        worker.error.connect(on_error)
        progress_dlg.canceled.connect(worker.terminate)
        worker.start()
        progress_dlg.exec()

    def closeEvent(self, event):
        self._player.cleanup()
        super().closeEvent(event)
