import random
from flask_client import FlaskClient
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
flask_client = FlaskClient()

def give_idea():
    FlaskClient.Twitch.send_message(f'{line1}{random.choice(ideas)} Game')
