import time as tm
import asyncio
import threading
import os
import settings
import pytchat
from twitchio.ext import commands as twitchcommands

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

            while self.yt_chat.is_alive():
                for c in self.yt_chat.get().sync_items():
                    self.chat_data.append(("Youtube", c.author.name, c.message))
                    print(f"[YT] {c.author.name}: {c.message}")

        self.youtube_thread = threading.Thread(target=run, daemon=True)
        self.youtube_thread.start()

chat = Chat()
thread1 = threading.Thread(target=chat.run)
thread1.start()
commands = {
    "!boss": [
        [lambda: boss_active],
        lambda: chat.send_message(f'Boss Isnt Available {name}'),
        [lambda: chat.send_message(f'Boss Health: {boss_hp}/{boss_max_hp}')]
    ],
    "!attack": [None],
    "!admin spawn": [None],
    "!admin kill": [None],
    "!admin heal": [None],
    "!admin hp": [None],
    "!idea": [None],
    "!donate": [None],
    "!serverhelpweb": [None],
    "!admin stop handler commands": [None],
    "!lurk": [None],
    "!unlurk": [None]
}
lurkers = {}
boss_active = False
boss_hp = 0
boss_max_hp = 1000
running = True
while running:
    old_chat_id = len(chat.chat_data)
    while True:
        if not len(chat.chat_data) == old_chat_id:
            platform = chat.chat_data[len(chat.chat_data)][0]
            name = chat.chat_data[len(chat.chat_data)][1]
            message = chat.chat_data[len(chat.chat_data)][2]
            break
        tm.sleep(0.1)
    if not commands[message][0][0] == None:
        for i in range(commands[message][0]):
            if commands[message][0][i]:
                pass
            else:
                break
        if not i == len(commands[message][0]):
            commands[message][1]()
        else:
            for i in range(len(commands[message][0][2])):
                commands[message][0][2][i]()
    else:
        for i in range(len(commands[message][0][2])):
            commands[message][0][1][i]()
