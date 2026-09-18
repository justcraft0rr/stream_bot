from start_bots import start_bots
from flask import Flask
from os import getenv
import tomllib
config = tomllib.load(open('/home/justcraft/config.toml', 'rb'))
flask = Flask(__name__)
stream_events = {'stream_id': 0}
bots = start_bots(
    twitch_refresh_token=getenv('twitch_refresh_token'),
    twitch_token_id=getenv('twitch_client_id'),
    twitch_token_secret=getenv('twitch_client_secret'),
    twitch_broadcaster=getenv('twitch_broadcaster'),
    twitch_bot=getenv('twitch_bot'),
    kick_client_id=getenv('kick_client_id'),
    kick_client_secret=getenv('kick_client_secret'),
    youtube_channel=getenv('youtube_channel'),
    obs_host=config['connection']['host'],
    obs_port=config['connection']['port'],
    obs_password=config['connection']['password'],
    gpt_api_key=getenv('gpt_api_key'),
    spotify_client_id=getenv('spotify_client_id'),
    spotify_client_secret=getenv('spotify_client_secret'),
    stream_events=stream_events,
    flask=flask
)
