from command_handler import start as start_handler
from utils import Timer, Chat
from obsws_python import ReqClient as OBS_HANDLER
from evdev import InputDevice, ecodes
from spotipy.oauth2 import SpotifyOAuth
import time as tm
import settings
import spotipy
import threading
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
obs = OBS_HANDLER()
timer = Timer()
keyboard = InputDevice('/dev/input/event3')
spotify = Spotify()

# Setup
obs.set_current_program_scene('Starting Soon')
spotify.set_volume(100)
obs.set_input_mute('Music', False)
obs.set_input_mute('Firefox', True)
obs.set_input_mute('Games', False)
obs.set_input_mute('Microphone', False)
obs.set_input_mute('Capture Card Sound', False)

# Start Stream
obs.start_stream()
threading.Thread(target=start_handler, daemon=True).start()

# Start Countdown
timer.countdown([0, 0, 1, 0, 0, 0])
while not timer.done:
    tm.sleep(0.01)
    obs.set_input_settings(
        'Timer Text',
        {'text': timer.formatted_time},
        overlay=True
    )

# Wait For Numpad *
for event in keyboard.read_loop():
    if event.type == ecodes.EV_KEY and event.value == 1:
        if event.code == ecodes.KEY_KPASTERISK:
            break

# Setup
obs.set_current_program_scene('Screen 1')
spotify.set_volume(70)

# Main Loop
for event in keyboard.read_loop():
    if event.type == ecodes.EV_KEY and event.value == 1:
        if event.code == ecodes.KEY_KPMINUS:
            break
        elif event.code == ecodes.KEY_KPSLASH:
            var = obs.get_current_program_scene().current_program_scene_name
            obs.set_current_program_scene('BRB')
            for event in keyboard.read_loop():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    if event.code == ecodes.KEY_KPSLASH:
                        break
            obs.set_current_program_scene(var)

# Setup
obs.set_current_program_scene('Ending Soon')
spotify.set_volume(100)
obs.set_input_mute('Music', False)
obs.set_input_mute('Firefox', True)
obs.set_input_mute('Games', False)
obs.set_input_mute('Microphone', False)
obs.set_input_mute('Capture Card Sound', False)

# Start Countdown
timer.countdown([0, 0, 1, 0, 0, 0])
while not timer.done:
    tm.sleep(0.01)
    obs.set_input_settings(
        'Timer Text',
        {'text': timer.formatted_time},
        overlay=True
    )

# Wait For Numpad *
for event in keyboard.read_loop():
    if event.type == ecodes.EV_KEY and event.value == 1:
        if event.code == ecodes.KEY_KPASTERISK:
            break

# Stop Stream
obs.stop_stream()
print('Stopped Stream')
