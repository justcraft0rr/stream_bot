from utils import Chat
import time as tm
lines = [
    "!admin hp ",
    "Does Not Exist",
    "Has Damaged The Boss By",
    "The Boss Is Now At"
]
commands = [
    "!boss",
    "!attack",
    "!admin spawn",
    "!admin kill",
    "!admin heal",
    "!admin hp",
    "!idea",
    "!donate",
    "!serverhelpweb",
    "!admin stop handler commands",
    "!lurk",
    "!unlurk"
]
lurkers = []
boss_active = False
boss_hp = 0
boss_max_hp = 1000
running = True
while running:
    old_chat_id = len(Chat.chat)
    while True:
        if not len(Chat.chat) == old_chat_id:
            platform = Chat.chat[len(Chat.chat)][0]
            name = Chat.chat[len(Chat.chat)][1]
            message = Chat.chat[len(Chat.chat)][2]
            break
        tm.sleep(0.1)
