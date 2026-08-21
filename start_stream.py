from obsws_python import ReqClient as OBS_HANDLER
from evdev import InputDevice, ecodes
from spotipy.oauth2 import SpotifyOAuth
from twitchio.ext import commands as twitchcommands
import time as tm
import settings
import spotipy
import threading
import asyncio
import os
import pytchat
import random


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
name = ""
args = []
obs = OBS_HANDLER()
timer = Timer()
keyboard = InputDevice('/dev/input/event3')
spotify = Spotify()
chat = Chat()


def boss_handler(action, value=None):
    global boss_active
    global boss_hp
    if action == "hp":
        boss_hp = max(0, min(value, boss_max_hp))
    elif action == "spawn":
        boss_active = True
        boss_hp = boss_max_hp
    elif action == "kill":
        boss_active = False
        boss_hp = 0


def attack_boss():
    global boss_hp
    damage = random.randint(25, 45)
    old_hp = boss_hp
    boss_hp -= damage
    if boss_hp <= 0:
        boss_hp = 0
        chat.send_message(
            f"💀 {name} dealt {damage} damage and defeated the boss!"
        )
        boss_handler("kill")
    else:
        chat.send_message(
            f"⚔️ {name} dealt {damage} damage! "
            f"Boss HP: {old_hp} -> {boss_hp}/{boss_max_hp}"
        )


def is_admin(username):
    username = username.lower()
    admins = [
        user.lower()
        for user in settings.admins
    ]
    broadcasters = [
        user.lower()
        for user in settings.broadcasters
    ]
    return (
        username in admins
        or username in broadcasters
    )


def has_exactly_one_argument():
    return len(args) == 1


def argument_is_integer():
    if len(args) != 1:
        return False
    try:
        int(args[0])
        return True
    except ValueError:
        return False


def hp_is_valid():
    if not argument_is_integer():
        return False
    hp = int(args[0])
    return 0 <= hp <= boss_max_hp


commands = {
    "!boss": {
        "checks": [
            lambda: boss_active
        ],
        "fail": lambda: chat.send_message(
            f"Boss Isn't Available, {name}!"
        ),
        "actions": [
            lambda: chat.send_message(
                f"Boss Health: "
                f"{boss_hp}/{boss_max_hp}"
            )
        ]
    },
    "!attack": {
        "checks": [
            lambda: boss_active
        ],
        "fail": lambda: chat.send_message(
            f"Boss Isn't Available, {name}!"
        ),
        "actions": [
            lambda: attack_boss()
        ]
    },
    "!admin spawn": {
        "checks": [
            lambda: not boss_active,
            lambda: is_admin(name)
        ],
        "fail": lambda: chat.send_message(
            f"Boss Is Already Spawned "
            f"Or You Aren't An Admin, {name}!"
        ),
        "actions": [
            lambda: boss_handler("spawn"),
            lambda: chat.send_message(
                f"Boss Spawned By {name}!"
            )
        ]
    },
    "!admin kill": {
        "checks": [
            lambda: boss_active,
            lambda: is_admin(name)
        ],
        "fail": lambda: chat.send_message(
            f"Boss Is Already Dead "
            f"Or You Aren't An Admin, {name}!"
        ),
        "actions": [
            lambda: boss_handler("kill"),
            lambda: chat.send_message(
                f"Boss Killed By {name}!"
            )
        ]
    },
    "!admin heal": {
        "checks": [
            lambda: boss_active,
            lambda: is_admin(name)
        ],
        "fail": lambda: chat.send_message(
            f"Boss Is Dead "
            f"Or You Aren't An Admin, {name}!"
        ),
        "actions": [
            lambda: boss_handler(
                "hp",
                boss_max_hp
            ),
            lambda: chat.send_message(
                f"Boss Healed To "
                f"{boss_max_hp} HP!"
            )
        ]
    },
    "!admin hp": {
        "checks": [
            lambda: boss_active,
            lambda: is_admin(name),
            lambda: has_exactly_one_argument(),
            lambda: hp_is_valid()
        ],
        "fail": lambda: chat.send_message(
            f"Usage: !admin hp <0-{boss_max_hp}> "
            f"(boss must be alive and you must be an admin)"
        ),
        "actions": [
            lambda: boss_handler(
                "hp",
                int(args[0])
            ),
            lambda: chat.send_message(
                f"Boss HP Set To "
                f"{boss_hp}/{boss_max_hp} "
                f"By {name}!"
            )
        ]
    },
    "!idea": {
        "checks": [],
        "fail": None,
        "actions": [
            lambda: chat.send_message(
                f"Justcraft Has To Make A {ideas[random.randrange(1, len(ideas))]} Game Cuz Of {name}"
            )
        ]
    },
    "!donate": {
        "checks": [],
        "fail": None,
        "actions": [chat.send_message(f'{name} Here Is My Donate Link: https://streamelements.com/justcraft_twitchy/tip')]
    },
    "!serverhelpweb": {
        "checks": [],
        "fail": None,
        "actions": [chat.send_message(f'{name} Here Is My Website: https://mcserverhelp.my.canva.site/')]
    },
    "!lurk": {
        "checks": [],
        "fail": None,
        "actions": [
            lambda: lurkers.__setitem__(
                name.lower(),
                True
            ),
            lambda: chat.send_message(
                f"{name} is now lurking!"
            )
        ]
    },
    "!unlurk": {
        "checks": [],
        "fail": None,
        "actions": [
            lambda: lurkers.pop(
                name.lower(),
                None
            ),
            lambda: chat.send_message(
                f"Welcome back, {name}!"
            )
        ]
    }
}


def process_command(username, message):
    global name
    global args
    name = username
    message = message.strip()
    if not message.startswith("!"):
        return
    command_name = None
    sorted_commands = sorted(
        commands.keys(),
        key=len,
        reverse=True
    )
    for possible_command in sorted_commands:
        if (
            message.lower() == possible_command.lower()
            or
            message.lower().startswith(
                possible_command.lower() + " "
            )
        ):
            command_name = possible_command
            break
    if command_name is None:
        return
    argument_text = message[
        len(command_name):
    ].strip()
    if argument_text:
        args = argument_text.split()
    else:
        args = []
    command = commands[command_name]
    checks = command["checks"]
    fail = command["fail"]
    actions = command["actions"]
    for check in checks:
        try:
            result = check()
        except Exception as e:
            print(
                f"Error checking "
                f"{command_name}: {e}"
            )
            return
        if not result:
            if fail is not None:
                try:
                    fail()
                except Exception as e:
                    print(
                        f"Error running fail "
                        f"for {command_name}: {e}"
                    )
            return


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
    if not chat.chat_data:
        tm.sleep(0.1)
        continue
    platform, username, message = (
        chat.chat_data.pop(0)
    )
    print(
        f"[COMMAND] "
        f"{platform} | "
        f"{username} | "
        f"{message}"
    )
    process_command(
        username,
        message
    )
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
