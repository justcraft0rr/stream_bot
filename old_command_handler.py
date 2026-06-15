from utils import sb
import idea_giver
import random
import time as tm
broadcasters = ["justcraft_twitchy"]
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
    "!admin stop handler commands"
]
line1 = "LMAO Someone Tried To Damage The Boss While It Ain't Here LMAO"
line2a1 = "Here is the donate link!"
line2a2 = "https://streamelements.com/justcraft_twitchy/tip"
line3a1 = "Here is the website for my servers help: "
line3a2 = "https://mcserverhelp.my.canva.site/"
line4 = "Is More Than The Max"
line5 = "!admin hp "
boss_active = False
boss_hp = 0
boss_max_hp = 1000
command = None
running = True
command = open("commands.txt", "r", encoding="utf-8").read()
parts = command.split(">")
chat_id = parts[0][1:]
name = parts[1][1:]
message = parts[2]
old_id = chat_id
while running:
    while True:
        tm.sleep(0.1)
        command = open("commands.txt", "r", encoding="utf-8").read()
        parts = command.split(">")
        chat_id = parts[0][1:]
        name = parts[1][1:]
        message = parts[2]
        if not old_id == chat_id and message[0] == "!":
            old_id = chat_id
            break
        old_id = chat_id
    part = message[0:10]
    if message[0] == "!" and message not in commands and not part == line5:
        print(part)
        sb.global_message(
            "bot",
            f'Command "{message[1:len(message)]}" Does Not Exist',
            None
        )
    elif message == "!boss":
        if boss_active:
            sb.global_message("bot", f"Boss HP: {boss_hp}/{boss_max_hp}", None)
        elif not boss_active:
            sb.global_message("bot", "The Boss Is Not Available", None)
    elif message == "!attack":
        if boss_active:
            damage = random.randint(10, 35)
            boss_hp -= damage
            if boss_hp <= 0:
                sb.global_message("bot", "Boss Defeated", "purple")
            else:
                sb.global_message(
                    "bot",
                    f"Someone Dealt {damage} Amount Of Damage",
                    None
                    )
        elif not boss_active:
            sb.global_message(
                "bot",
                line1,
                None
                )
    elif message == "!admin spawn" and name in broadcasters:
        if boss_active:
            sb.global_message("bot", "Boss Is Already Active", None)
        elif not boss_active:
            boss_max_hp = 10000
            boss_hp = boss_max_hp
            boss_active = True
            sb.global_message("bot", "Boss Started", "purple")
    elif message == "!admin kill" and name in broadcasters:
        if boss_active:
            boss_active = False
            sb.global_message(
                "bot",
                f"{name} Killed The Boss With The Ban Hammer",
                None
            )
        elif not boss_active:
            sb.global_message(
                "bot",
                "Boss Already Dead",
                None
            )
    elif message == "!admin heal" and name in broadcasters:
        if boss_active:
            boss_hp = boss_max_hp
            sb.global_message(
                "bot",
                "Boss Healed",
                None
            )
    elif message[0:10] == "!admin hp " and name in broadcasters:
        yes = int(message[11:len(message)])
        try:
            if yes <= boss_max_hp and boss_active is True:
                boss_hp = int(message[11:len(message)])
                sb.global_message(
                    "bot",
                    f"Set Boss HP To {boss_hp}",
                    None
                )
            elif int(message[11:len(message)]) <= boss_max_hp:
                sb.global_message(
                    "bot",
                    f"{int(message[11:len(message)])} {line4} {boss_max_hp}",
                    None
                )
            elif not boss_active:
                sb.global_message(
                    "bot",
                    "Boss Is Not Started Yet",
                    None
                )
        except ValueError:
            sb.global_message(
                "bot",
                f"Value {message[11:len(message)]} Isn't a Number",
                None
            )
    elif message == "!idea":
        idea_giver.give_idea()
    elif message == "!donate":
        sb.global_message(
            "bot",
            line2a1 + line2a2,
            None
        )
    elif message == "!serverhelpweb":
        sb.global_message(
            "bot",
            line3a1 + line3a2,
            None
        )
    elif message == "!admin stop handler commands" and name in broadcasters:
        break
