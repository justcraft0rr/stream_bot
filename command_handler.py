import asyncio
import os
import random
import threading
import time as tm

import pytchat
import settings
from twitchio.ext import commands as twitchcommands


# ============================================================
# GLOBAL VARIABLES
# ============================================================

boss_active = False
boss_hp = 0
boss_max_hp = 1000

lurkers = {}

# Current command information
name = ""
args = []


# ============================================================
# BOSS FUNCTIONS
# ============================================================

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


# ============================================================
# ADMIN CHECK
# ============================================================

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


# ============================================================
# ARGUMENT CHECKS
# ============================================================

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


# ============================================================
# TWITCH / YOUTUBE CHAT
# ============================================================

class Chat(twitchcommands.Bot):

    def __init__(self):

        twitch_token = os.getenv("twitch_token")
        twitch_channel = os.getenv("twitch_channel")

        if not twitch_token:
            raise RuntimeError(
                "Missing environment variable: twitch_token"
            )

        if not twitch_channel:
            raise RuntimeError(
                "Missing environment variable: twitch_channel"
            )

        super().__init__(
            token=f"oauth:{twitch_token}",
            prefix="!",
            initial_channels=[twitch_channel]
        )

        self.chat_data = []

        self.youtube_thread = None
        self.yt_chat = None

        self.ready = False

    # ========================================================
    # YOUTUBE VIDEO ID
    # ========================================================

    def extract_video_id(self, text):

        text = text.strip()

        if "v=" in text:
            return text.split("v=")[1].split("&")[0]

        if "youtu.be/" in text:
            return text.split("youtu.be/")[1].split("?")[0]

        if "youtube.com/live/" in text:
            return text.split("youtube.com/live/")[1].split("?")[0]

        return text

    # ========================================================
    # TWITCH READY
    # ========================================================

    async def event_ready(self):

        print("Twitch Connected!")

        self.ready = True

    # ========================================================
    # TWITCH MESSAGE
    # ========================================================

    async def event_message(self, message):

        if message.echo:
            return

        if message.author is None:
            return

        username = message.author.name
        content = message.content.strip()

        self.chat_data.append(
            (
                "Twitch",
                username,
                content
            )
        )

        print(
            f"[TWITCH] {username}: {content}"
        )

        # Only broadcaster can start YouTube chat
        if username.lower() in [
            user.lower()
            for user in settings.broadcasters
        ]:

            if content.lower().startswith("!yt "):

                raw = content[4:].strip()

                if not raw:
                    return

                video_id = self.extract_video_id(raw)

                print(
                    f"Starting YouTube chat for: {video_id}"
                )

                self.start_youtube(video_id)

    # ========================================================
    # SEND TWITCH MESSAGE
    # ========================================================

    def send_message(self, message):

        twitch_channel = os.getenv("twitch_channel")

        if not twitch_channel:
            print(
                "Cannot send message: "
                "twitch_channel is missing"
            )
            return

        channel = self.get_channel(twitch_channel)

        if channel is None:
            print(
                "Cannot send message: "
                "channel not found"
            )
            return

        try:

            asyncio.run_coroutine_threadsafe(
                channel.send(message),
                self.loop
            )

        except Exception as e:

            print(
                f"Failed to send Twitch message: {e}"
            )

    # ========================================================
    # START YOUTUBE CHAT
    # ========================================================

    def start_youtube(self, video_id):

        # Stop old YouTube chat
        if self.yt_chat is not None:

            try:
                self.yt_chat.terminate()

            except Exception:
                pass

        try:

            self.yt_chat = pytchat.create(
                video_id=video_id
            )

        except Exception as e:

            print(
                f"Failed to connect to YouTube: {e}"
            )

            return

        def run():

            print("YouTube Connected!")

            try:

                while self.yt_chat.is_alive():

                    for message in (
                        self.yt_chat
                        .get()
                        .sync_items()
                    ):

                        username = message.author.name
                        content = message.message

                        self.chat_data.append(
                            (
                                "Youtube",
                                username,
                                content
                            )
                        )

                        print(
                            f"[YT] "
                            f"{username}: "
                            f"{content}"
                        )

                    tm.sleep(0.1)

            except Exception as e:

                print(
                    f"YouTube chat error: {e}"
                )

            print(
                "YouTube Chat Stopped"
            )

        self.youtube_thread = threading.Thread(
            target=run,
            daemon=True
        )

        self.youtube_thread.start()


# ============================================================
# CREATE CHAT BOT
# ============================================================

chat = Chat()


# ============================================================
# COMMANDS
#
# checks:
#     EVERY check must return True
#
# fail:
#     Runs when ANY check returns False
#
# actions:
#     Runs when ALL checks return True
# ============================================================

commands = {

    # ========================================================
    # !boss
    # ========================================================

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


    # ========================================================
    # !attack
    # ========================================================

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


    # ========================================================
    # !admin spawn
    # ========================================================

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


    # ========================================================
    # !admin kill
    # ========================================================

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


    # ========================================================
    # !admin heal
    # ========================================================

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


    # ========================================================
    # !admin hp <value>
    #
    # Example:
    #
    # !admin hp 500
    # ========================================================

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


    # ========================================================
    # !idea
    # ========================================================

    "!idea": {

        "checks": [],

        "fail": None,

        "actions": [
            lambda: chat.send_message(
                f"Send your idea, {name}!"
            )
        ]
    },


    # ========================================================
    # !donate
    # ========================================================

    "!donate": {

        "checks": [],

        "fail": None,

        "actions": []
    },


    # ========================================================
    # !serverhelpweb
    # ========================================================

    "!serverhelpweb": {

        "checks": [],

        "fail": None,

        "actions": []
    },


    # ========================================================
    # !lurk
    # ========================================================

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


    # ========================================================
    # !unlurk
    # ========================================================

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


# ============================================================
# COMMAND PARSER
# ============================================================

def process_command(username, message):

    global name
    global args

    name = username

    message = message.strip()

    if not message.startswith("!"):
        return

    # --------------------------------------------------------
    # Find the longest matching command
    #
    # This is important because:
    #
    # !admin hp
    #
    # must be detected as "!admin hp"
    # instead of "!admin"
    # --------------------------------------------------------

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

    # Unknown command
    if command_name is None:
        return

    # --------------------------------------------------------
    # Get arguments
    # --------------------------------------------------------

    argument_text = message[
        len(command_name):
    ].strip()

    if argument_text:
        args = argument_text.split()

    else:
        args = []

    # --------------------------------------------------------
    # Get command
    # --------------------------------------------------------

    command = commands[command_name]

    checks = command["checks"]
    fail = command["fail"]
    actions = command["actions"]

    # --------------------------------------------------------
    # CHECKS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # ALL CHECKS PASSED
    # --------------------------------------------------------

    for action in actions:

        try:

            action()

        except Exception as e:

            print(
                f"Error running action "
                f"for {command_name}: {e}"
            )


# ============================================================
# START TWITCH
# ============================================================

def start_bot():

    try:

        chat.run()

    except Exception as e:

        print(
            f"Twitch bot crashed: {e}"
        )


thread1 = threading.Thread(
    target=start_bot,
    daemon=True
)

thread1.start()


# ============================================================
# MAIN LOOP
# ============================================================

running = True

print("Command handler started!")

while running:

    # Wait for a message
    if not chat.chat_data:

        tm.sleep(0.1)

        continue

    # Get oldest message
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
