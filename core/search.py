from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp


class SearchWorker(QThread):
    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, query: str, platform: str, parent=None):
        super().__init__(parent)
        self.query = query
        self.platform = platform  # "youtube", "soundcloud", or "both"

    def run(self):
        results = []
        try:
            if self.platform in ("youtube", "both"):
                results += _search("ytsearch10", self.query, "youtube")
            if self.platform in ("soundcloud", "both"):
                results += _search("scsearch10", self.query, "soundcloud")
            self.results_ready.emit(results)
        except Exception as e:
            self.error.emit(str(e))


def _get_thumbnail(entry: dict, platform: str) -> str:
    # Try plain string field first
    t = entry.get("thumbnail")
    if isinstance(t, str) and t.startswith("http"):
        return t
    # Try thumbnails list — iterate in reverse (higher res at end)
    thumbs = entry.get("thumbnails")
    if isinstance(thumbs, list) and thumbs:
        for th in reversed(thumbs):
            if not isinstance(th, dict):
                continue
            url = th.get("url", "")
            if isinstance(url, str) and url.startswith("http"):
                return url
    # YouTube fallback: construct reliable thumbnail URL from video ID
    if platform == "youtube":
        vid_id = entry.get("id", "")
        if vid_id:
            return f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"
    return ""


def _search(prefix: str, query: str, platform: str) -> list[dict]:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    url = f"{prefix}:{query}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries", []) if info else []
    results = []
    for e in entries:
        if not e:
            continue
        duration = e.get("duration") or 0
        results.append({
            "title": e.get("title", "Unknown"),
            "url": e.get("url") or e.get("webpage_url", ""),
            "thumbnail": _get_thumbnail(e, platform),
            "duration": int(duration),
            "platform": platform,
            "uploader": e.get("uploader") or e.get("channel", ""),
            "id": e.get("id", ""),
        })
    return results


def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
