import os
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp


class DownloadWorker(QThread):
    progress = pyqtSignal(int)        # 0-100
    status = pyqtSignal(str)          # status text
    finished = pyqtSignal(str)        # output file path
    failed = pyqtSignal(str)          # error message

    def __init__(self, url: str, output_dir: str, fmt: str, title: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.output_dir = output_dir
        self.fmt = fmt        # "mp3" or "flac"
        self.title = title
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)

        postprocessors = []
        if self.fmt == "mp3":
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            })
        else:
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": "flac",
            })
        postprocessors.append({"key": "FFmpegMetadata"})
        postprocessors.append({"key": "EmbedThumbnail"})

        opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "postprocessors": postprocessors,
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._hook],
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                ext = self.fmt
                safe_title = ydl.prepare_filename(info).rsplit(".", 1)[0]
                out_path = f"{safe_title}.{ext}"
            self.finished.emit(out_path)
        except Exception as e:
            if not self._cancelled:
                self.failed.emit(str(e))

    def _hook(self, d: dict):
        if self._cancelled:
            raise Exception("Cancelled")
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                pct = int(downloaded / total * 100)
                self.progress.emit(pct)
            speed = d.get("_speed_str", "")
            eta = d.get("_eta_str", "")
            self.status.emit(f"Downloading… {speed} ETA {eta}")
        elif status == "finished":
            self.progress.emit(99)
            self.status.emit("Processing…")
