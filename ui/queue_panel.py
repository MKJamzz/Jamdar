from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QScrollArea, QPushButton,
)
from PyQt6.QtCore import Qt
from core.downloader import DownloadWorker
import config


class QueueItem(QWidget):
    def __init__(self, title: str, worker: DownloadWorker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self._build(title)
        worker.progress.connect(self._on_progress)
        worker.status.connect(self._on_status)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)

    def _build(self, title: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        info = QVBoxLayout()
        info.setSpacing(2)
        self._title = QLabel(title[:60])
        self._title.setStyleSheet("font-weight: bold;")
        info.addWidget(self._title)

        self._status = QLabel("Queued…")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        info.addWidget(self._status)

        layout.addLayout(info, stretch=1)

        right = QVBoxLayout()
        right.setSpacing(2)
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedWidth(160)
        self._bar.setFixedHeight(14)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(
            "QProgressBar { border: 1px solid #444; border-radius: 3px; background: #2a2a2a; }"
            "QProgressBar::chunk { background: #2196F3; border-radius: 2px; }"
        )
        right.addWidget(self._bar)

        self._pct_lbl = QLabel("0%")
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._pct_lbl.setStyleSheet("font-size: 11px; color: #aaa;")
        right.addWidget(self._pct_lbl)

        layout.addLayout(right)

        self._cancel_btn = QPushButton("✕")
        self._cancel_btn.setFixedSize(24, 24)
        self._cancel_btn.setToolTip("Cancel")
        self._cancel_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #666; font-size: 14px; }"
            "QPushButton:hover { color: #cc4444; }"
        )
        self._cancel_btn.clicked.connect(self._cancel)
        layout.addWidget(self._cancel_btn)

        self.setStyleSheet(
            "QueueItem { background: #1e1e1e; border-radius: 4px; border: 1px solid #2a2a2a; }"
        )

    def _on_progress(self, pct: int):
        self._bar.setValue(pct)
        self._pct_lbl.setText(f"{pct}%")

    def _on_status(self, text: str):
        self._status.setText(text)

    def _on_finished(self, path: str):
        self._bar.setValue(100)
        self._bar.setStyleSheet(
            "QProgressBar { border: 1px solid #2a5a2a; border-radius: 3px; background: #1a2a1a; }"
            "QProgressBar::chunk { background: #4CAF50; border-radius: 2px; }"
        )
        self._pct_lbl.setText("100%")
        self._status.setText("Done ✓")
        self._cancel_btn.setEnabled(False)

    def _on_failed(self, err: str):
        self._status.setText(f"Failed: {err[:60]}")
        self._bar.setStyleSheet(
            "QProgressBar { border: 1px solid #5a2a2a; border-radius: 3px; background: #2a1a1a; }"
            "QProgressBar::chunk { background: #F44336; border-radius: 2px; }"
        )
        self._cancel_btn.setEnabled(False)

    def _cancel(self):
        self.worker.cancel()
        self._status.setText("Cancelled")
        self._cancel_btn.setEnabled(False)


class QueuePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: list[DownloadWorker] = []
        self._active = 0
        self._pending: list[tuple] = []  # (result, fmt, title)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QHBoxLayout()
        lbl = QLabel("DOWNLOAD QUEUE")
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;")
        header.addWidget(lbl)
        header.addStretch()
        clear_btn = QPushButton("Clear done")
        clear_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #555; font-size: 11px; }"
            "QPushButton:hover { color: #888; }"
        )
        clear_btn.clicked.connect(self._clear_done)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._items_widget = QWidget()
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setSpacing(4)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.addStretch()
        scroll.setWidget(self._items_widget)
        layout.addWidget(scroll)

    def enqueue(self, result: dict, fmt: str, output_dir: str):
        title = result.get("title", "Unknown")
        self._pending.append((result["url"], fmt, title, output_dir))
        self._drain()

    def _drain(self):
        max_concurrent = config.get("max_concurrent_downloads") or 3
        while self._pending and self._active < max_concurrent:
            url, fmt, title, output_dir = self._pending.pop(0)
            self._start_download(url, fmt, title, output_dir)

    def _start_download(self, url: str, fmt: str, title: str, output_dir: str):
        worker = DownloadWorker(url, output_dir, fmt, title)
        self._workers.append(worker)
        self._active += 1

        item = QueueItem(f"{title}  [{fmt.upper()}]", worker)
        self._items_layout.insertWidget(self._items_layout.count() - 1, item)

        worker.finished.connect(lambda _: self._slot_freed())
        worker.failed.connect(lambda _: self._slot_freed())
        worker.start()

    def _slot_freed(self):
        self._active = max(0, self._active - 1)
        self._drain()

    def _clear_done(self):
        layout = self._items_layout
        for i in reversed(range(layout.count() - 1)):  # skip stretch
            item = layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QueueItem):
                    status = w._status.text()
                    if status.startswith("Done") or status.startswith("Failed") or status.startswith("Cancelled"):
                        layout.removeItem(item)
                        w.deleteLater()
