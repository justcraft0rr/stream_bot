import settings, spotipy
from spotipy.oauth2 import SpotifyOAuth
class Spotify:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-read-playback-state user-modify-playback-state"
        ))

    # ▶️ Play a song by name
    def play_song(self, song_name):
        results = self.sp.search(q=song_name, type="track", limit=10)

        items = results.get("tracks", {}).get("items", [])
        if not items:
            return "No song found."

        # try to find exact match first
        song_name_lower = song_name.lower()

        exact_match = None
        for track in items:
            if track["name"].lower() == song_name_lower:
                exact_match = track
                break

        # fallback to first result if no exact match
        track = exact_match if exact_match else items[0]

        uri = track["uri"]
        self.sp.start_playback(uris=[uri])

        return f"Playing: {track['name']} - {track['artists'][0]['name']}"

    # 🎧 Get currently playing song
    def get_current_song(self):
        current = self.sp.current_playback()

        if not current or not current.get("item"):
            return "Nothing is currently playing."

        item = current["item"]
        return f"{item['name']} - {item['artists'][0]['name']}"

    # 🔊 Set playback volume (0-100)
    def set_volume(self, volume):
        self.sp.volume(volume)


spotify = Spotify()
spotify.set_volume(100)