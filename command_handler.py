from utils import sb, QOL
import time as tm
broadcasters = {
    "twitch": "justcraft_twitchy",
    "youtube": "justcraft-i8q"
}
admins = {
    "twitch": [
        "core0fcraft4",
        "egriga",
        "jarpi_is_seal",
        "thelittlenoob_pc"
    ]
}
lines = [
    "!admin hp "
]
commands = [
    ""
]
boss_active = False
boss_hp = 0
boss_max_hp = 1000
running = True
message = QOL.read_file("commands.txt")
parts = message.split(">")
chat_id = parts[0][1:]
name = parts[1][1:]
platform = parts[2][1:]
message = parts[3]
old_id = chat_id
running = True
while running:
    while True:
        message = QOL.read_file("commands.txt")
        parts = message.split(">")
        chat_id = parts[0][1:]
        name = parts[1][1:]
        platform = parts[2][1:]
        message = parts[3]
        part = message[0:10]
        if not old_id == chat_id and message[0] == "!":
            old_id = chat_id
            break
        elif message not in commands and not part == lines[0]:
            sb.global_message(
                "bot",
                f'Command "{message[1:len(message)]}" Does Not Exist {name}',
                None
            )
        old_id = chat_id
        tm.sleep(0.1)
