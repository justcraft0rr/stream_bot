import os
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import obsws_python
import spotipy
from spotipy.oauth2 import SpotifyOAuth
class Elevenlabs:
    def __init__(self):
        self.obs = obsws_python.ReqClient()
        self.elevenlabs = ElevenLabs(api_key=os.getenv('elevenlabs_api_key'))

    def tts(self, text, voice_id="TX3LPaxmHKxFdv7VOQHJ", model_id="eleven_v3", speed=1.0):
        audio = self.elevenlabs.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=VoiceSettings(
                speed=speed
            )
        )
        with open("tts.mp3", "wb") as f:
            for chunk in audio:
                f.write(chunk)
        self.obs.set_input_settings(
            name="Elevenlabs",
            settings={
                "local_file": "/home/justcraft/Projects/stream_bot/tts.mp3"
            },
            overlay=True
        )
        # self.obs.trigger_media_input_action(
        #     "Elevenlabs",
        #     "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
        # )
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('spotify_client_id'),
    client_secret=os.getenv('spotify_client_secret'),
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-modify-playback-state user-read-playback-state"
))
# Search for All Star
results = sp.search(q="All Star Smash Mouth", type="track", limit=1)
track = results["tracks"]["items"][0]
# elevenlabs = Elevenlabs()
# all_star = '''Somebody once told me the world is gonna roll me
# I ain't the sharpest tool in the shed
# She was looking kind of dumb with her finger and her thumb
# In the shape of an "L" on her forehead
# Well, the years start comin' and they don't stop comin'
# Fed to the rules and I hit the ground runnin'
# Didn't make sense not to live for fun
# Your brain gets smart, but your head gets dumb
# So much to do, so much to see
# So, what's wrong with taking the backstreets?
# You'll never know if you don't go (go)
# You'll never shine if you don't glow
# Hey now, you're an all-star
# Get your game on, go play
# Hey now, you're a rock star
# Get the show on, get paid
# (And all that glitters is gold)
# Only shootin' stars break the mold
# It's a cool place, and they say it gets colder
# You're bundled up now, wait 'til you get older
# But the meteor men beg to differ
# Judging by the hole in the satellite picture
# The ice we skate is gettin' pretty thin
# The water's gettin' warm, so you might as well swim
# My world's on fire, how 'bout yours?
# That's the way I like it, and I'll never get bored
# Hey now, you're an all-star
# Get your game on, go play
# Hey now, you're a rock star
# Get the show on, get paid
# (All that glitters is gold)
# Only shootin' stars break the mold
# Go for the moon
# (Go, go, go) go for the moon
# (Go, go, go) go for the moon
# Go (go), go for the moon
# Hey now, you're an all-star
# Get your game on, go play
# Hey now, you're a rock star
# Get the show on, get paid
# (And all that glitters is gold)
# Only shooting stars
# Somebody once asked, "Could I spare some change for gas?
# I need to get myself away from this place"
# I said, "Yep, what a concept, I could use a little fuel myself
# And we could all use a little change"
# Well, the years start comin' and they don't stop comin'
# Fed to the rules and I hit the ground runnin'
# Didn't make sense not to live for fun
# Your brain gets smart, but your head gets dumb
# So much to do, so much to see
# So, what's wrong with taking the backstreets?
# You'll never know if you don't go (go!)
# You'll never shine if you don't glow
# Hey now, you're an all-star
# Get your game on, go play
# Hey now, you're a rock star
# Get the show on, get paid
# (And all that glitters is gold)
# Only shootin' stars break the mold
# Only shootin' stars break the mold
# Go for the moon
# Go for the moon
# Go for the moon
# This is how we do it'''
# elevenlabs.tts(all_star, speed=0.1)



# Start playing it
sp.start_playback(uris=[track["uri"]])
obsws_python.ReqClient().trigger_media_input_action(
    "Elevenlabs",
    "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
)