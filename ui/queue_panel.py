from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QScrollArea, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.downloader import DownloadWorker
import config

# ── colour tokens ──────────────────────────────────────────────────────────────
INK        = "#221C2B"
INK_2      = "#6E6577"
SURFACE    = "#FFFFFF"
LINE       = "#ECE3DC"
LINE_2     = "#E0D5CC"
CORAL      = "#FF82A8"
CORAL_DEEP = "#E85684"

DONE_BG    = "#DEF6E6"
DONE_BDR   = "#cdeed8"
DONE_INK   = "#1a8c47"
FAIL_BG    = "#FDECEE"
FAIL_BDR   = "#F6D2D7"
FAIL_INK   = "#d23b4e"


# ══════════════════════════════════════════════════════════════════════════════
#  QueueItem
# ══════════════════════════════════════════════════════════════════════════════

class QueueItem(QWidget):
    def __init__(self, result: dict, fmt: str, worker: DownloadWorker, parent=None):
        super().__init__(parent)
        self._result  = result
        self._fmt     = fmt
        self.worker   = worker
        self._done    = False
        self._build(result.get("title", "Unknown"), fmt)
        worker.progress.connect(self._on_progress)
        worker.status.connect(self._on_status)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)

    def _build(self, title: str, fmt: str):
        self.setStyleSheet(self._card_style("active"))
        self.setMinimumHeight(72)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(6)

        # Top row: title + format chip + cancel button
        top = QHBoxLayout()
        top.setSpacing(8)

        self._title_lbl = QLabel(title[:55])
        self._title_lbl.setStyleSheet(
            f"font-weight: 600; font-size: 13px; color: {INK}; background: transparent;"
        )
        top.addWidget(self._title_lbl, stretch=1)

        fmt_text = f"MP3·320" if fmt == "mp3" else "FLAC"
        fmt_chip = QLabel(fmt_text)
        fmt_chip.setFixedHeight(18)
        fmt_chip.setStyleSheet(
            f"font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: 600; "
            f"color: {INK_2}; background: #F0E8E4; border-radius: 4px; padding: 0 5px;"
        )
        top.addWidget(fmt_chip)

        self._action_btn = QPushButton("✕")
        self._action_btn.setFixedSize(22, 22)
        self._action_btn.setToolTip("Cancel")
        self._action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_btn.setStyleSheet(
            f"QPushButton {{ background: #F0E8E4; border: none; border-radius: 11px; "
            f"color: {INK_2}; font-size: 12px; }}"
            f"QPushButton:hover {{ background: {FAIL_BDR}; color: {FAIL_INK}; }}"
        )
        self._action_btn.clicked.connect(self._cancel)
        top.addWidget(self._action_btn)
        root.addLayout(top)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(7)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(
            f"QProgressBar {{ border: none; border-radius: 3px; background: #EFE7E1; }}"
            f"QProgressBar::chunk {{ background: qlineargradient("
            f"x1:0,y1:0,x2:1,y2:0,stop:0 {CORAL},stop:1 {CORAL_DEEP}); border-radius: 3px; }}"
        )
        root.addWidget(self._bar)

        # Status row
        status_row = QHBoxLayout()
        self._status_lbl = QLabel("Queued…")
        self._status_lbl.setStyleSheet(f"color: {INK_2}; font-size: 11px; background: transparent;")
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()
        self._pct_lbl = QLabel("0%")
        self._pct_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono', monospace; font-size: 11px; "
            f"color: {INK_2}; background: transparent;"
        )
        status_row.addWidget(self._pct_lbl)
        root.addLayout(status_row)

    # ── state handlers ──────────────────────────────────────────────────────

    def _on_progress(self, pct: int):
        self._bar.setValue(pct)
        self._pct_lbl.setText(f"{pct}%")
        self._status_lbl.setText("Downloading…")

    def _on_status(self, text: str):
        self._status_lbl.setText(text)

    def _on_finished(self, path: str):
        self._done = True
        self._bar.setValue(100)
        self._bar.setStyleSheet(
            f"QProgressBar {{ border: none; border-radius: 3px; background: {DONE_BDR}; }}"
            f"QProgressBar::chunk {{ background: {DONE_INK}; border-radius: 3px; }}"
        )
        self._pct_lbl.setText("100%")
        self._status_lbl.setText(f"<font color='{DONE_INK}'>✓ Saved to drive</font>")
        self._status_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.setStyleSheet(self._card_style("done"))

        self._action_btn.setText("📂")
        self._action_btn.setToolTip("Reveal in file manager")
        self._action_btn.setStyleSheet(
            f"QPushButton {{ background: {DONE_BDR}; border: none; border-radius: 11px; "
            f"color: {DONE_INK}; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {DONE_INK}; color: white; }}"
        )
        import os
        self._action_btn.clicked.disconnect()
        self._action_btn.clicked.connect(lambda: self._reveal(path))

    def _on_failed(self, err: str):
        self._bar.setValue(0)
        self._bar.setStyleSheet(
            f"QProgressBar {{ border: none; border-radius: 3px; background: {FAIL_BDR}; }}"
            f"QProgressBar::chunk {{ background: {FAIL_INK}; border-radius: 3px; }}"
        )
        self._pct_lbl.setText("")
        self._status_lbl.setText(f"<font color='{FAIL_INK}'>⚠ Source unavailable</font>")
        self._status_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.setStyleSheet(self._card_style("fail"))

        self._action_btn.setText("↺")
        self._action_btn.setToolTip("Retry")
        self._action_btn.setStyleSheet(
            f"QPushButton {{ background: {FAIL_BDR}; border: none; border-radius: 11px; "
            f"color: {FAIL_INK}; font-size: 14px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {FAIL_INK}; color: white; }}"
        )
        self._action_btn.clicked.disconnect()
        self._action_btn.clicked.connect(self._retry)

    def _cancel(self):
        self.worker.cancel()
        self._status_lbl.setText("Cancelled")
        self._action_btn.setEnabled(False)

    def _retry(self):
        out = config.get("output_dir") or ""
        fmt = self._fmt
        self.worker = DownloadWorker(
            self._result["url"], out, fmt, self._result.get("title", "Unknown")
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.status.connect(self._on_status)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self._bar.setValue(0)
        self._bar.setStyleSheet(
            f"QProgressBar {{ border: none; border-radius: 3px; background: #EFE7E1; }}"
            f"QProgressBar::chunk {{ background: qlineargradient("
            f"x1:0,y1:0,x2:1,y2:0,stop:0 {CORAL},stop:1 {CORAL_DEEP}); border-radius: 3px; }}"
        )
        self._status_lbl.setText("Retrying…")
        self.setStyleSheet(self._card_style("active"))
        self._action_btn.setText("✕")
        self._action_btn.setToolTip("Cancel")
        self._action_btn.setStyleSheet(
            f"QPushButton {{ background: #F0E8E4; border: none; border-radius: 11px; "
            f"color: {INK_2}; font-size: 12px; }}"
            f"QPushButton:hover {{ background: {FAIL_BDR}; color: {FAIL_INK}; }}"
        )
        self._action_btn.clicked.disconnect()
        self._action_btn.clicked.connect(self._cancel)
        self.worker.start()

    @staticmethod
    def _reveal(path: str):
        import subprocess, os
        folder = os.path.dirname(path)
        try:
            subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

    @staticmethod
    def _card_style(state: str) -> str:
        if state == "done":
            return (
                f"QueueItem {{ background: {DONE_BG}; border-radius: 12px; "
                f"border: 1px solid {DONE_BDR}; }}"
            )
        if state == "fail":
            return (
                f"QueueItem {{ background: {FAIL_BG}; border-radius: 12px; "
                f"border: 1px solid {FAIL_BDR}; }}"
            )
        return (
            f"QueueItem {{ background: {SURFACE}; border-radius: 12px; "
            f"border: 1px solid {LINE}; }}"
        )

    def is_finished(self) -> bool:
        t = self._status_lbl.text()
        return self._done or "Cancelled" in t or "⚠" in t


# ══════════════════════════════════════════════════════════════════════════════
#  QueuePanel
# ══════════════════════════════════════════════════════════════════════════════

class QueuePanel(QWidget):
    active_count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: list[DownloadWorker] = []
        self._active  = 0
        self._pending: list[tuple] = []  # (result, fmt, output_dir)
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"QueuePanel {{ background: {SURFACE}; border-left: 1px solid {LINE}; }}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(
            f"background: {SURFACE}; border-bottom: 1px solid {LINE};"
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 12, 0)
        h_lay.setSpacing(8)

        title = QLabel("Downloads")
        title.setStyleSheet(
            f"font-family: 'Bricolage Grotesque 96pt ExtraBold', sans-serif; font-size: 15px; "
            f"font-weight: 700; color: {INK}; background: transparent;"
        )
        h_lay.addWidget(title)

        self._badge = QLabel("0 active")
        self._badge.setFixedHeight(20)
        self._badge.setStyleSheet(
            f"background: #FFE6EE; color: {CORAL_DEEP}; font-size: 11px; font-weight: 600; "
            "border-radius: 10px; padding: 0 8px;"
        )
        self._badge.hide()
        h_lay.addWidget(self._badge)
        h_lay.addStretch()

        clear_btn = QPushButton("Clear done")
        clear_btn.setFixedHeight(26)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {INK_2}; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {INK}; }}"
        )
        clear_btn.clicked.connect(self._clear_done)
        h_lay.addWidget(clear_btn)

        root.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._items_widget = QWidget()
        self._items_widget.setStyleSheet("background: transparent;")
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setSpacing(6)
        self._items_layout.setContentsMargins(10, 10, 10, 10)
        self._items_layout.addStretch()
        scroll.setWidget(self._items_widget)
        root.addWidget(scroll)

    # ── public API ──────────────────────────────────────────────────────────

    def enqueue(self, result: dict, fmt: str, output_dir: str):
        self._pending.append((result, fmt, output_dir))
        self._drain()

    # ── internals ──────────────────────────────────────────────────────────

    def _drain(self):
        max_c = config.get("max_concurrent_downloads") or 3
        while self._pending and self._active < max_c:
            result, fmt, output_dir = self._pending.pop(0)
            self._start(result, fmt, output_dir)

    def _start(self, result: dict, fmt: str, output_dir: str):
        title = result.get("title", "Unknown")
        worker = DownloadWorker(result["url"], output_dir, fmt, title)
        self._workers.append(worker)
        self._active += 1
        self._emit_count()

        item = QueueItem(result, fmt, worker)
        self._items_layout.insertWidget(self._items_layout.count() - 1, item)

        worker.finished.connect(lambda _: self._slot_freed())
        worker.failed.connect(lambda _: self._slot_freed())
        worker.start()

    def _slot_freed(self):
        self._active = max(0, self._active - 1)
        self._emit_count()
        self._drain()

    def _emit_count(self):
        self.active_count_changed.emit(self._active)
        if self._active > 0:
            self._badge.setText(f"{self._active} active")
            self._badge.show()
        else:
            self._badge.hide()

    def _clear_done(self):
        layout = self._items_layout
        for i in reversed(range(layout.count() - 1)):
            item = layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QueueItem):
                w: QueueItem = item.widget()
                if w.is_finished():
                    layout.removeItem(item)
                    w.deleteLater()
