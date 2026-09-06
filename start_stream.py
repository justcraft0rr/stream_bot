from evdev import InputDevice, ecodes
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from dotenv import load_dotenv
from twitchio.ext import commands as twitchcommands
from obsws_python import ReqClient as OBS_HANDLER
import time as tm
import twitchio
import settings
import spotipy
import threading
import asyncio
import os
import pytchat
import random
import requests
import re


class GPT:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

    def ask(self, prompt):
        response = self.client.chat.completions.create(
            model="openai/gpt-5",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content


class Timer():
    def __init__(self):
        self.done = None
        self.time = [0, 0, 0, 0, 0, 0]
        self.formatted_time = '00:00'
    @staticmethod
    def time_to_ms(time: list):
        return (
            time[0] + 
            time[1] * 100 + 
            time[2] * 100 * 60 + 
            time[3] * 100 * 60 * 60 + 
            time[4] * 100 * 60 * 60 * 24 + 
            time[5] * 100 * 60 * 60 * 24 * 365
        )
    @staticmethod
    def convert_milliseconds(total_milliseconds: int):
        second = 100
        minute = second * 60
        hour = minute * 60
        day = hour * 24
        year = day * 365

        years = total_milliseconds // year
        total_milliseconds %= year

        days = total_milliseconds // day
        total_milliseconds %= day

        hours = total_milliseconds // hour
        total_milliseconds %= hour

        minutes = total_milliseconds // minute
        total_milliseconds %= minute

        seconds = total_milliseconds // second
        milliseconds = total_milliseconds % second

        return [milliseconds, seconds, minutes, hours, days, years]
    @staticmethod
    def format_time(time: list):
        # [milliseconds, seconds, minutes, hours, days, years]

        highest = next(
            (i for i in range(len(time) - 1, 1, -1) if time[i] != 0),
            1
        )

        parts = time[:highest + 1][::-1]

        return ":".join(f"{x:02}" for x in parts)
    def countdown(self, start: list):
        def run():
            self.done = False
            self.time = start
            self.formatted_time = str(self.format_time(self.time))
            while True:
                if self.time == [0, 0, 0, 0, 0, 0]:
                    break
                tm.sleep(0.01)
                self.time = self.convert_milliseconds(self.time_to_ms(self.time)-1)
                self.formatted_time = self.format_time(self.time)
            self.done = True
        threading.Thread(target=run, daemon=True).start()
    def timer(self, end: list):
        def run():
            self.done = False
            self.time = [0, 0, 0, 0, 0, 0]
            self.formatted_time = str(self.format_time(self.time))
            while True:
                if self.time == end:
                    break
                tm.sleep(0.01)
                self.time = self.convert_milliseconds(self.time_to_ms(self.time)+1)
                self.formatted_time = self.format_time(self.time)
            self.done = True
        threading.Thread(target=run, daemon=True).start()


class Spotify:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('spotify_client_id'),
            client_secret=os.getenv('spotify_client_secret'),
            redirect_uri='http://127.0.0.1:8888/callback',
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


try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


class Chat(twitchcommands.Bot):
    def __init__(self):
        self.refresh_twitch_token()
        super().__init__(
            token=f'oauth:{os.getenv('twitch_token')}',
            prefix="!",
            initial_channels=[os.getenv('twitch_channel')]
        )

        self.chat_data = []
        self.stream_events = []
        self.youtube_thread = None
        self.yt_chat = None
        self.ready = False

    # ---------------- UTIL ----------------
    def extract_video_id(self, text: str):
        text = text.strip()

        if "v=" in text:
            return text.split("v=")[1].split("&")[0]

        if "youtu.be/" in text:
            return text.split("youtu.be/")[1].split("?")[0]

        return text

    def refresh_twitch_token(self):
        client_id = os.getenv("twitch_client_id")
        client_secret = os.getenv("twitch_client_secret")
        refresh_token = os.getenv("twitch_refresh_token")
        if not client_id or not client_secret or not refresh_token:
            raise RuntimeError(
                "Missing twitch_client_id, twitch_client_secret, or twitch_refresh_token"
            )

        response = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

        response.raise_for_status()
        data = response.json()

        access_token = data["access_token"]
        new_refresh_token = data.get("refresh_token", refresh_token)

        # Read .bashrc
        bashrc = os.path.expanduser("~/.bashrc")

        with open(bashrc, "r") as f:
            content = f.read()

        # Update ONLY the token variables
        content = re.sub(
            r"^export twitch_token=.*$",
            f'export twitch_token="{access_token}"',
            content,
            flags=re.MULTILINE,
        )

        content = re.sub(
            r"^export twitch_refresh_token=.*$",
            f'export twitch_refresh_token="{new_refresh_token}"',
            content,
            flags=re.MULTILINE,
        )

        # Write .bashrc back
        with open(bashrc, "w") as f:
            f.write(content)

        return access_token

    # ---------------- TWITCH ----------------
    async def event_ready(self):
        print("Twitch Connected!")
        self.ready = True
    
    async def event_follow(self, payload):
        username = payload.user.name
        self.stream_events.append(('Twitch', 'Follow', username))

    async def event_message(self, message):
        if message.echo:
            return

        user = message.author.name
        content = message.content

        self.chat_data.append(("Twitch", user, content))
        print(f"[TWITCH] {user}: {content}")

        # ONLY YOU CAN CONTROL IT
        if user.lower() in settings.broadcasters:

            # command: !yt <link or id>
            if content.startswith("!yt "):
                raw = content[4:]
                video_id = self.extract_video_id(raw)

                print(f"Starting YouTube chat for: {video_id}")

                self.start_youtube(video_id)
    
    def send_message(self, message):
        channel = self.get_channel(os.getenv('twitch_channel'))

        if channel:
            asyncio.run_coroutine_threadsafe(
                channel.send(message),
                self.loop
            )

    # ---------------- YOUTUBE ----------------
    def start_youtube(self, video_id):
        # stop old thread if needed
        self.yt_chat = pytchat.create(video_id=video_id)

        def run():
            print("YouTube Connected!")

            chat_stuff = self.chat_data
            while self.yt_chat.is_alive():
                for c in self.yt_chat.get().sync_items():
                    chat_stuff.append(("Youtube", c.author.name, c.message))
                    print(f"[YT] {c.author.name}: {c.message}")

        self.youtube_thread = threading.Thread(target=run, daemon=True)
        self.youtube_thread.start()


load_dotenv()
boss_active = False
boss_hp = 0
boss_max_hp = 1000
lurkers = {}
ideas = [
    "Flappy Bird",
    "Multiplayer Dodge Arena",
    "Simple Platformer",
    "Maze",
    "Cookie Clicker",
    "Space Shooter",
    "Pong With Power-Ups",
    "Multiplayer Tag",
    "Memory Matching",
    "Sword Duel"
]
obs = OBS_HANDLER()
timer = Timer()
keyboard = InputDevice('/dev/input/event2')
spotify = Spotify()
chat = Chat()
gpt = GPT(os.environ['gpt_api_key'])


def command_handler():
    while True:
        try:
            if thread1 == None:
                pass
            break
        except Exception:
            pass
    old_chat_id = len(chat.chat_data)
    while True:
        while True:
            if old_chat_id == len(chat.chat_data):
                platform = chat.chat_data[len(chat.chat_data)][0]
                user = chat.chat_data[len(chat.chat_data)][1]
                message = chat.chat_data[len(chat.chat_data)][2]
                break
            old_chat_id = len(chat.chat_data)
        if user not in settings.admins and user not in settings.broadcasters:
            if message == '!boss':
                if boss_active:
                    chat.send_message(f'Boss Health: {boss_hp}/{boss_max_hp}')
                else:
                    chat.send_message(f"Boss Isn't Available")
            elif message == '!attack':
                if boss_active:
                    damage = random.randint(25, 40)
                    old_hp = boss_hp
                    boss_hp -= damage
                    chat.send_message(f'Boss Got Damaged By {damage} HP Was At {old_hp}/{boss_max_hp} Now At {boss_hp}/{boss_max_hp}')
                else:
                    chat.send_message("Boss Isn't Available")
        elif user in settings.admins or user in settings.broadcasters:
            if message == '!admin spawn':
                if boss_active:
                    chat.send_message('Boss Is Already Active')
                else:
                    chat.send_message(f'Boss Spawned By {user}')
                    boss_active = True
            elif message == '!admin kill':
                if boss_active:
                    chat.send_message(f'Boss Got Killed By {user}')
                    boss_active = False
                    boss_hp = boss_max_hp
                else:
                    chat.send_message('Boss Is Not Active')
            elif message == '!admin heal':
                if boss_active:
                    if boss_hp == boss_max_hp:
                        chat.send_message('Boss Is Already Full Health')
                    else:
                        chat.send_message(f'Boss Got Healed Back To {boss_max_hp}')
                        boss_hp = boss_max_hp
                else:
                    chat.send_message('Boss Is Not Active')
            elif message[0:10] == '!admin hp ':
                new_hp = message[10:len(message)]


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
thread1 = threading.Thread(target=chat.run, daemon=True)
thread1.start()

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
