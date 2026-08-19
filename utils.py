import os
import obsws_python
import requests
from twitchio.ext import commands as twitchcommands
import pytchat
import threading
import asyncio
import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time as tm


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
        super().__init__(
            token=f'oauth:{os.getenv('twitch_token')}',
            prefix="!",
            initial_channels=[os.getenv('twitch_channel')]
        )

        self.chat_data = []
        self.youtube_thread = None
        self.yt_chat = None
        self.chat = []
        self.ready = False

    # ---------------- UTIL ----------------
    def extract_video_id(self, text: str):
        text = text.strip()

        if "v=" in text:
            return text.split("v=")[1].split("&")[0]

        if "youtu.be/" in text:
            return text.split("youtu.be/")[1].split("?")[0]

        return text

    # ---------------- TWITCH ----------------
    async def event_ready(self):
        print("Twitch Connected!")
        self.ready = True

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
        channel = self.get_channel(settings.initial_channel)

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


if __name__ == '__main__':
    #obs = obsws_python.ReqClient()
    spotify = Spotify()
    timer = Timer()
    chat = Chat()
    thread1 = threading.Thread(target=chat.run)
    thread1.start()
    while not chat.ready:
        pass
    chat.send_message('text')

