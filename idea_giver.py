import random
from utils import sb
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
    "Sword Duel",
]
line1 = "Justcraft has to make a "


def give_idea():
    sb.global_message(
        "bot",
        f"{line1}{ideas[random.randrange(1, len(ideas))]} Game",
        "orange",
    )
