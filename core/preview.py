import os
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp
import pygame


_pygame_init = False


def _ensure_pygame():
    global _pygame_init
    if not _pygame_init:
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        _pygame_init = True


class PreviewWorker(QThread):
    ready = pyqtSignal(str)          # path to temp audio file
    duration_ready = pyqtSignal(float)  # track duration in seconds
    error = pyqtSignal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            tmp = tempfile.mktemp(suffix=".mp3")
            opts = {
                "format": "bestaudio/best",
                "outtmpl": tmp.replace(".mp3", ".%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }],
                "download_ranges": lambda _info, _: [{"start_time": 0, "end_time": 30}],
                "force_keyframes_at_cuts": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])

            # Locate the output file (postprocessor may change extension)
            if not os.path.exists(tmp):
                base = tmp.replace(".mp3", "")
                for ext in ("mp3", "m4a", "opus", "webm"):
                    candidate = f"{base}.{ext}"
                    if os.path.exists(candidate):
                        tmp = candidate
                        break

            # Read actual duration via mutagen
            duration = 30.0
            try:
                from mutagen import File as MutaFile
                audio = MutaFile(tmp)
                if audio and audio.info:
                    duration = float(audio.info.length)
            except Exception:
                pass

            self.ready.emit(tmp)
            self.duration_ready.emit(duration)
        except Exception as e:
            self.error.emit(str(e))


class Player:
    def __init__(self):
        _ensure_pygame()
        self._current_file: str | None = None
        self._paused = False

    def play(self, path: str):
        self.stop()
        self._current_file = path
        self._paused = False
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

    def pause(self):
        if pygame.mixer.music.get_busy() and not self._paused:
            pygame.mixer.music.pause()
            self._paused = True

    def resume(self):
        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False

    def stop(self):
        if pygame.mixer.music.get_busy() or self._paused:
            pygame.mixer.music.stop()
        self._paused = False

    def is_playing(self) -> bool:
        return pygame.mixer.music.get_busy() and not self._paused

    def is_paused(self) -> bool:
        return self._paused

    def get_position_ms(self) -> int:
        return pygame.mixer.music.get_pos()

    def set_position(self, seconds: float):
        pygame.mixer.music.set_pos(seconds)

    def cleanup(self):
        self.stop()
        if self._current_file and os.path.exists(self._current_file):
            try:
                os.remove(self._current_file)
            except OSError:
                pass
        self._current_file = None
