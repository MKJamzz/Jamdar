import re
import requests
from PyQt6.QtCore import QThread, pyqtSignal
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import config

_ANON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def extract_playlist_id(url: str) -> str | None:
    m = re.search(r"playlist/([A-Za-z0-9]+)", url)
    return m.group(1) if m else None


class SpotifyImportWorker(QThread):
    playlist_ready = pyqtSignal(str, object)   # playlist_name, [(track_name, artists), ...]
    error = pyqtSignal(str)

    def __init__(self, playlist_url: str, parent=None):
        super().__init__(parent)
        self.playlist_url = playlist_url

    def run(self):
        playlist_id = extract_playlist_id(self.playlist_url)
        if not playlist_id:
            self.error.emit("Could not parse a playlist ID from that URL.")
            return

        client_id = config.get("spotify_client_id")
        client_secret = config.get("spotify_client_secret")

        try:
            if client_id and client_secret:
                sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret,
                ))
                name, tracks = _fetch_playlist(sp, playlist_id)
            else:
                name, tracks = _fetch_playlist_anon(playlist_id)
        except Exception as e:
            self.error.emit(f"Spotify error: {e}")
            return

        self.playlist_ready.emit(name, tracks)


# ── spotipy (developer credentials) path ──────────────────────────────────────

def _fetch_playlist(sp: spotipy.Spotify, playlist_id: str) -> tuple[str, list[tuple[str, str]]]:
    info = sp.playlist(playlist_id, fields="name")
    name = info.get("name", "Spotify Playlist")
    tracks = _fetch_all_tracks(sp, playlist_id)
    return name, tracks


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


# ── anonymous (no developer account needed) path ──────────────────────────────

def _get_anon_token() -> str:
    resp = requests.get(
        "https://open.spotify.com/get_access_token",
        headers=_ANON_HEADERS,
        params={"reason": "transport", "productType": "web_player"},
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json().get("accessToken")
    if not token:
        raise ValueError("Spotify did not return an anonymous access token")
    return token


def _fetch_playlist_anon(playlist_id: str) -> tuple[str, list[tuple[str, str]]]:
    token = _get_anon_token()
    auth_headers = {**_ANON_HEADERS, "Authorization": f"Bearer {token}"}

    resp = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}",
        headers=auth_headers,
        params={"fields": "name"},
        timeout=10,
    )
    resp.raise_for_status()
    name = resp.json().get("name", "Spotify Playlist")

    tracks = []
    offset = 0
    while True:
        r = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            headers=auth_headers,
            params={
                "offset": offset,
                "limit": 100,
                "fields": "items(track(name,artists(name))),next",
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        for item in items:
            track = item.get("track")
            if not track:
                continue
            track_name = track.get("name", "")
            artists = ", ".join(a["name"] for a in track.get("artists", []))
            if track_name:
                tracks.append((track_name, artists))
        if not data.get("next"):
            break
        offset += len(items)

    return name, tracks
