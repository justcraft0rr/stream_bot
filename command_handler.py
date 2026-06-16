from utils import sb, Chat
import time as tm
import random
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
    if message == commands[0]:
        if boss_active:
            sb.global_message(
                "bot",
                f"Boss HP: {boss_hp}/{boss_max_hp}",
                None,
                platform
            )
        elif not boss_active:
            sb.global_message(
                "bot",
                f"The Boss Is Not Available {name}",
                None,
                platform
            )
    elif message == commands[1]:
        if boss_active:
            damage = random.randint(10, 45)
            boss_hp -= damage
            if boss_hp <= 0:
                sb.global_message(
                    "bot",
                    f"Boss Has Been Killed By {name}",
                    None,
                    platform
                )
            else:
                part_1 = f"{name} {lines[2]} {damage}"
                sb.global_message(
                    "bot",
                    f"{part_1} {lines[3]} {boss_hp}/{boss_max_hp}",
                    None,
                    platform
                )
