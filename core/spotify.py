import re
from PyQt6.QtCore import QThread, pyqtSignal
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import config


def extract_playlist_id(url: str) -> str | None:
    m = re.search(r"playlist/([A-Za-z0-9]+)", url)
    return m.group(1) if m else None


class SpotifyImportWorker(QThread):
    track_found = pyqtSignal(str, str)   # search_query, display_name
    progress = pyqtSignal(int, int)      # current, total
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, playlist_url: str, parent=None):
        super().__init__(parent)
        self.playlist_url = playlist_url

    def run(self):
        client_id = config.get("spotify_client_id")
        client_secret = config.get("spotify_client_secret")

        if not client_id or not client_secret:
            self.error.emit(
                "Spotify credentials not configured.\n"
                "Go to Settings and add your Spotify Client ID and Secret.\n\n"
                "Get them free at: developer.spotify.com/dashboard"
            )
            return

        playlist_id = extract_playlist_id(self.playlist_url)
        if not playlist_id:
            self.error.emit("Could not parse a playlist ID from that URL.")
            return

        try:
            sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
            ))
            tracks = _fetch_all_tracks(sp, playlist_id)
        except Exception as e:
            self.error.emit(f"Spotify error: {e}")
            return

        total = len(tracks)
        for i, (name, artists) in enumerate(tracks):
            query = f"{name} {artists}"
            display = f"{name} — {artists}"
            self.progress.emit(i + 1, total)
            self.track_found.emit(query, display)

        self.finished.emit()


def _fetch_all_tracks(sp: spotipy.Spotify, playlist_id: str) -> list[tuple[str, str]]:
    tracks = []
    offset = 0
    while True:
        page = sp.playlist_items(
            playlist_id,
            offset=offset,
            fields="items.track(name,artists.name),next",
            additional_types=["track"],
        )
        items = page.get("items", [])
        for item in items:
            track = item.get("track")
            if not track:
                continue
            name = track.get("name", "")
            artists = ", ".join(a["name"] for a in track.get("artists", []))
            if name:
                tracks.append((name, artists))
        if not page.get("next"):
            break
        offset += len(items)
    return tracks
