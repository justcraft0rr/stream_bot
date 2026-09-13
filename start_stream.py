from start_bots import start_bots
from flask import Flask
from os import getenv
import tomllib
config = tomllib.load(open('/home/justcraft/config.toml', 'rb'))
flask = Flask(__name__)
bots = start_bots(
    twitch_refresh_token=getenv('twitch_refresh_token'),
    twitch_token_id=getenv('twitch_token_id'),
    twitch_token_secret=getenv('twitch_token_secret'),
    twitch_broadcaster=getenv('twitch_broadcaster'),
    twitch_bot=getenv('twitch_bot'),
    youtube_channel=getenv('youtube_channel'),
    obs_host=config['connection']['host'],
    obs_port=config['connection']['port'],
    obs_password=config['connection']['password'],
    gpt_api_key=getenv('gpt_api_key'),
    spotify_client_id=getenv('spotify_client_id'),
    spotify_client_secret=getenv('spotify_client_secret'),
    flask=flask
)
