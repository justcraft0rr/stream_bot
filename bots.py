import requests
import asyncio
import os
import re
import json
from datetime import datetime
from twitchio.ext import commands
from twitchio import eventsub
from flask import request
from openai import OpenAI
from spotipy.oauth2 import SpotifyOAuth
import pytchat
import obsws_python
import spotipy
class TwithBot(commands.Bot):
    def __init__(self, **kwargs):
        self.requirements = {
            'twitch_refresh_token': kwargs.get('twitch_refresh_token'),
            'twitch_token_id': kwargs.get('twitch_token_id'),
            'twitch_token_secret': kwargs.get('twitch_token_secret'),
            'twitch_broadcaster': kwargs.get('twitch_broadcaster'),
            'twitch_bot': kwargs.get('twitch_bot'),
            'flask': kwargs.get('flask')
        }
        self.refresh_twitch_token(
            self.requirements['twitch_token_id'],
            self.requirements['twitch_token_secret'],
            self.requirements['twitch_refresh_token']
        )
        super().__init__(
            token=f'oauth:{self.refresh_twitch_token(
                self.requirements['twitch_token_id'],
                self.requirements['twitch_token_secret'],
                self.requirements['twitch_refresh_token']
            )}',
            prefix='!',
            initial_channels=[self.requirements['twitch_broadcaster']]
        )

        self.ready = False
        self.stream_id = 0
        self.stream_events = {}
        self.eventsub = eventsub.EventSubWSClient(self)
        self.connector = '≋'
        self.flask = self.requirements['flask']
        self.flask.add_url_rule(
            '/twitch/stream-info',
            'stream-info',
            self.stream
        )
        self.flask.add_url_rule(
            '/twitch/status',
            'status',
            self.status
        )
        self.flask.add_url_rule(
            '/twitch/start',
            'start',
            self.run
        )
        self.flask.add_url_rule(
            '/twitch/stop',
            'stop',
            self.stop,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/reload',
            'reload',
            self.reload,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/user/<username>',
            'user',
            self.flask_user,
            methods=['GET']
        )
        self.flask.add_url_rule(
            '/twitch/events',
            'events',
            self.events
        )
        self.flask.add_url_rule(
            '/twitch/send_message',
            'send_message',
            self.flask_send_message,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/ban',
            'ban',
            self.flask_ban,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/unban',
            'unban',
            self.flask_unban,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/timeout',
            'timeout',
            self.flask_timeout,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/create-clip',
            'create-clip',
            self.flask_create_clip,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/add-moderator',
            'add-moderator',
            self.flask_add_moderator,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/remove-moderator',
            'remove-moderator',
            self.flask_remove_moderator,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/add-vip',
            'add-vip',
            self.flask_vip,
            methods=['POST']
        )
        self.flask.add_url_rule(
            '/twitch/remove-vip',
            'remove-vip',
            self.flask_remove_vip,
            methods=['POST']
        )
    
    # Main Stuff

    def run(self):
        super().run()
    
    def refresh_twitch_token(self, client_id, client_secret, refresh_token):
        if not client_id or not client_secret or not refresh_token:
            raise RuntimeError(
                'Missing twitch_client_id, twitch_client_secret, or twitch_refresh_token'
            )

        response = requests.post(
            'https://id.twitch.tv/oauth2/token',
            params={
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            },
        )

        response.raise_for_status()
        data = response.json()

        access_token = data['access_token']
        new_refresh_token = data.get('refresh_token', refresh_token)

        # Read .bashrc
        bashrc = os.path.expanduser('~/.bashrc')

        with open(bashrc, 'r') as f:
            content = f.read()

        # Update ONLY the token variables
        content = re.sub(
            r'^export twitch_token=.*$',
            f'export twitch_token={"'"}{access_token}{"'"}',
            content,
            flags=re.MULTILINE,
        )

        content = re.sub(
            r'^export twitch_refresh_token=.*$',
            f'export twitch_refresh_token={"'"}{new_refresh_token}{"'"}',
            content,
            flags=re.MULTILINE,
        )

        # Write .bashrc back
        with open(bashrc, 'w') as f:
            f.write(content)

        return access_token

    async def event_ready(self):
        self.ready = True
        await self.eventsub.subscribe_channel_follows_v2(
            broadcaster=await self.fetch_user(self.requirements['twitch_broadcaster']).id,
            moderator=await self.fetch_user(self.requirements['twitch_bot']).id
        )
        asyncio.create_task(self.live_handle())
    
    async def event_eventsub_notification_followV2(
        self,
        event: eventsub.ChannelFollowData
    ):
        self.stream_events[self.stream_id+1] = {'event': 'follow', 'username': event.user.name}
        self.stream_id += 1
    
    def event_message(self, message):
        self.stream_events[self.stream_id+1] = {'event': 'message', 'username': message.author.name, 'message': message.content}
        self.stream_id += 1
    
    async def is_live(self):
        streams = await self.fetch_streams(
            user_logins=[self.requirements['twitch_broadcaster']]
        )

        return len(streams) > 0
    
    async def get_stream(self):
        streams = await self.fetch_streams(
            user_logins=[self.requirements['twitch_broadcaster']]
        )

        if not streams:
            return None

        return streams[0]
    
    def send_message(self, message):
        channel = self.get_channel(self.requirements['twitch_broadcaster'])

        if channel:
            asyncio.run_coroutine_threadsafe(
                channel.send(message),
                self.loop
            )
    
    async def live_handle(self):
        old_state = await self.is_live()
        while True:
            if self.ready:
                state = await self.is_live()
                if not old_state == state and not state:
                    json.dump(
                        self.stream_events,
                        open(f'{datetime.now().strftime(f'%Y-%m-%d{self.connector}%H:%M:%S')}{self.connector}chat{self.connector}live.json', 'w'),
                        indent=4
                    )
                    self.stream_events = {}
                    self.stream_id = 0
                old_state = state
                await asyncio.sleep(30)
    
    async def get_followers(self):
        follows = await self.fetch_users_follows(
            to_id=await self.fetch_user(
                self.requirements['twitch_broadcaster']
            ).id
        )

        return follows
    
    async def get_user(self, username):
        return await self.fetch_user(username)
    
    async def get_channel(self):
        return await self.fetch_channel(
            self.requirements['twitch_broadcaster']
        )
    
    async def ban(self, username, reason=None):
        user = await self.get_user(username)

        await self.ban_user(
            broadcaster=self.requirements['twitch_broadcaster'],
            moderator=self.requirements['twitch_bot'],
            user=user.id,
            reason=reason
        )
    
    async def unban(self, username):
        user = await self.get_user(username)

        await self.unban_user(
            broadcaster=self.requirements['twitch_broadcaster'],
            moderator=self.requirements['twitch_bot'],
            user=user.id
        )
    
    async def timeout(self, username, duration, reason=None):
        user = await self.get_user(username)

        await self.ban_user(
            broadcaster=self.requirements['twitch_broadcaster'],
            moderator=self.requirements['twitch_bot'],
            user=user.id,
            duration=duration,
            reason=reason
        )
    
    async def get_moderators(self):
        return await self.fetch_moderators(
            broadcaster=self.requirements['twitch_broadcaster']
        )
    
    async def add_moderator(self, username):
        user = await self.get_user(username)

        return await self.add_channel_moderator(
            broadcaster=self.requirements['twitch_broadcaster'],
            user=user.id
        )
    
    async def remove_moderator(self, username):
        user = await self.get_user(username)

        return await self.remove_channel_moderator(
            broadcaster=self.requirements['twitch_broadcaster'],
            user=user.id
        )
    
    async def get_vips(self):
        return await self.fetch_vips(
            broadcaster=self.requirements['twitch_broadcaster']
        )
    
    async def add_vip(self, username):
        user = await self.get_user(username)

        return await self.add_channel_vip(
            broadcaster=self.requirements['twitch_broadcaster'],
            user=user.id
        )
    
    async def remove_vip(self, username):
        user = await self.get_user(username)

        return await self.remove_channel_vip(
            broadcaster=self.requirements['twitch_broadcaster'],
            user=user.id
        )
    
    async def make_clip(self):
        return await self.create_clip(
            broadcaster=self.requirements['twitch_broadcaster']
        )
    
    async def make_prediction(self, title, outcomes, duration):
        return await self.create_prediction(
            broadcaster=self.requirements['twitch_broadcaster'],
            title=title,
            outcomes=outcomes,
            prediction_window=duration
        )
    
    async def make_poll(self, title, choices, duration):
        return await self.create_poll(
            broadcaster=self.requirements['twitch_broadcaster'],
            title=title,
            choices=choices,
            duration=duration
        )
    
    def stop(self):
        asyncio.run_coroutine_threadsafe(
            self.close(),
            self.loop
        )
    
    def reload(self):
        async def reload():
            await self.close()
            await self.connect()

        asyncio.run_coroutine_threadsafe(
            reload(),
            self.loop
        ).result()
    
    # Flask Stuff

    def stream(self):
        stream = asyncio.run_coroutine_threadsafe(
            self.get_stream(),
            self.loop
        ).result()

        if stream is None:
            return {'live': False}

        return {
            'live': True,
            'id': stream.id,
            'user_id': stream.user_id,
            'user_name': stream.user_name,
            'game_id': stream.game_id,
            'game_name': stream.game_name,
            'title': stream.title,
            'viewer_count': stream.viewer_count,
            'started_at': stream.started_at.isoformat(),
            'language': stream.language,
            'thumbnail_url': stream.thumbnail_url,
            'type': stream.type
        }
    
    def status(self):
        return {
            'ready': self.ready,
            'live': self.is_live()
        }
    
    def events(self):
        return self.stream_events
    
    def flask_user(self, username):
        user = asyncio.run_coroutine_threadsafe(
            self.get_user(username),
            self.loop
        ).result()

        if user is None:
            return {'error': 'User not found'}, 404

        return {
            'id': user.id,
            'username': user.name,
            'display_name': user.display_name,
            'description': user.description,
            'profile_image_url': user.profile_image_url,
            'offline_image_url': user.offline_image_url,
            'created_at': user.created_at.isoformat(),
            'view_count': user.view_count
        }
    
    def flask_send_message(self):
        data = request.json

        message = data.get('message')

        if not message:
            return {'error': 'Missing message'}, 400

        self.send_message(message)
    
    def flask_ban(self):
        data = request.json
        username = data.get('username')
        reason = data.get('reason')
        self.ban(username, reason)
    
    def flask_unban(self):
        data = request.json
        username = data.get('username')
        self.unban(username)
    
    def flask_timeout(self):
        data = request.json
        username = data.get('username')
        duration = data.get('duration')
        reason = data.get('reason')
        self.timeout(username, duration, reason)
    
    def flask_create_clip(self):
        self.make_clip()
    
    def flask_add_moderator(self):
        data = request.json
        username = data.get('username')
        self.add_moderator(username)
    
    def flask_vip(self):
        data = request.json
        username = data.get('username')
        self.add_vip(username)
    
    def flask_remove_moderator(self):
        data = request.json
        username = data.get('username')
        self.remove_moderator(username)
    
    def flask_remove_vip(self):
        data = request.json
        username = data.get('username')
        self.remove_vip(username)

class YoutubeBot:
    def __init__(self, **kwargs):
        self.requirements = {
            'youtube_channel': kwargs.get('youtube_channel'),
            'flask': kwargs.get('flask')
        }

        self.chat = pytchat.create(
            video_id=self.get_stream()
        )
        asyncio.create_task(self.live_handle())
        self.stream_events = {}
        self.stream_id = 0
        self.flask = self.requirements['flask']
    
    def get_stream(self):
        channel = self.requirements['youtube_channel']
        if not channel.startswith('http'):
            channel = f'https://www.youtube.com/@{channel}'
        response = requests.get(
            channel,
            headers={
                'User-Agent': 'Mozilla/5.0'
            }
        )
        response.raise_for_status()
        match = re.search(
            rf'{"'"}videoId{"'"}:{"'"}([A-Za-z0-9_-]{"{"}11{"}"}){"'"}',
            response.text
        )
        if not match:
            return None
        return match.group(1)
    
    def is_live(self):
        return self.get_stream() is not None
    
    async def live_handle(self):
        while self.chat.is_alive():
            for message in self.chat.get().sync_items():
                self.stream_events[self.stream_id+1] = {
                    'event': 'message',
                    'username': message.author.name,
                    'message': message.message
                }
                self.stream_id += 1

            await asyncio.sleep(1)

class OBS:
    def __init__(self, **kwargs):
        self.requirements = {
            'obs_host': kwargs.get('obs_host'),
            'obs_port': kwargs.get('obs_port'),
            'obs_password': kwargs.get('obs_password'),
            'flask': kwargs.get('flask')
        }
        self.obs = obsws_python.ReqClient(
            host=self.requirements['obs_host'],
            port=self.requirements['obs_port'],
            password=self.requirements['obs_password']
        )
        self.flask = self.requirements['flask']
        self.flask.add_url_rule(
            '/obs/get/scenes',
            'get_scenes',
            self.obs.get_scene_list
        )
        self.flask.add_url_rule(
            '/obs/get/program_scene',
            'current_program_scene',
            self.obs.get_current_program_scene
        )
        self.flask.add_url_rule(
            '/obs/set/program_scene',
            'set_program_scene',
            self.set_program_scene,
            methods=['post']
        )
        self.flask.add_url_rule(
            '/obs/get/scene_item_list',
            'get_item_list',
            self.obs.get_scene_item_list
        )
        self.flask.add_url_rule(
            '/obs/get/scene_item_id',
            'get_scene_item_id',
            self.obs.get_scene_item_id
        )
    
    def set_program_scene(self):
        data = request.json
        scene = data.get('scene')
        self.obs.set_current_program_scene(scene)

class GPT:
    def __init__(self, **kwargs):
        self.requirements = {
            'gpt_api_key': kwargs.get('gpt_api_key'),
            'flask': kwargs.get('flask')
        }
        self.client = OpenAI(
            base_url='https://openrouter.ai/api/v1',
            api_key=self.requirements['gpt_api_key']
        )
    
    def ask(self, prompt):
        response = self.client.chat.completions.create(
            model="openai/gpt-5",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

class Spotify:
    def __init__(self, **kwargs):
        self.requirements = {
            'spotify_client_id': kwargs.get('spotify_client_id'),
            'spotify_client_secret': kwargs.get('spotify_client_secret'),
            'flask': kwargs.get('flask')
        }
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.requirements['spotify_client_id'],
            client_secret=self.requirements['spotify_client_secret'],
            redirect_uri='http://127.0.0.1:8888/callback',
            scope="user-read-playback-state user-modify-playback-state playlist-read-private"
        ))
        self.flask = self.requirements['flask']
        self.flask.add_url_rule(
            '/spotify/get/current_song',
            'get_current_song',
            self.current_song
        )
        self.flask.add_url_rule(
            '/spotify/get/playlist',
            'get_playlist',
            self.get_playlist
        )
        self.flask.add_url_rule(
            '/spotify/get/playlist_tracks',
            'get_playlist_tracks',
            self.get_playlist_tracks
        )
        self.flask.add_url_rule(
            '/spotify/mediacontrol/play',
            'play',
            self.play
        )
        self.flask.add_url_rule(
            '/spotify/mediacontrol/pause',
            'pause',
            self.pause
        )
        self.flask.add_url_rule(
            '/spotify/mediacontrol/next',
            'next',
            self.next
        )
        self.flask.add_url_rule(
            '/spotify/mediacontrol/previous',
            'previous',
            self.previous
        )
        self.flask.add_url_rule(
            '/spotify/play/song'
            'play_song',
            self.play_song
        )
        self.flask.add_url_rule(
            '/spotify/play/playlist',
            'play_playlist',
            self.play_playlist
        )
        self.flask.add_url_rule(
            '/spotify/get/devices',
            'get_devices',
            self.get_devices
        )
        self.flask.add_url_rule(
            '/spotify/change_device',
            'change_device',
            self.change_device
        )
        self.flask.add_url_rule(
            '/spotify/change_device_by_name',
            'change_device_by_name',
            self.change_device_by_name
        )
        self.flask.add_url_rule(
            '/spotify/search/song',
            'search_song',
            self.search_song
        )
        self.flask.add_url_rule(
            '/spotify/queue/add_song',
            'add_song_to_queue',
            self.add_to_queue
        )
    
    def add_to_queue(self):
        data = request.json
        track_uri = data.get('track_uri')
        try:
            device_id = data.get('device_id')
        except:
            device_id = None
        self.sp.add_to_queue(
            uri=track_uri,
            device_id=device_id
        )
    
    def search_song(self):
        data = request.json
        query = data.get('query')
        results = self.sp.search(q=query, type="track", limit=1)

        if not results["tracks"]["items"]:
            return None

        return results["tracks"]["items"][0]
    
    def play_song(self):
        data = request.json
        track_uri = data.get('track_uri')
        try:
            device_id = data.get('device_id')
        except:
            device_id = None
        self.sp.start_playback(
            device_id=device_id,
            uris=[track_uri]
        )


    def play_playlist(self):
        data = request.json
        playlist_id = data.get('playlist_id')
        try:
            device_id = data.get('device_id')
        except:
            device_id = None
        self.sp.start_playback(
            device_id=device_id,
            context_uri=f"spotify:playlist:{playlist_id}"
        )


    def get_devices(self):
        return self.sp.devices()["devices"]


    def change_device(self):
        data = request.json
        device_id = data.get('device_id')
        try:
            play = data.get('play')
        except:
            play = False
        self.sp.transfer_playback(
            device_id=device_id,
            force_play=play
        )


    def change_device_by_name(self):
        data = request.json
        name = data.get('name')
        try:
            play = data.get('play')
        except:
            play = False
        devices = self.get_devices()

        for device in devices:
            if device["name"].lower() == name.lower():
                self.change_device(device["id"], play)
                return device

        return None

    def current_song(self):
        playback = self.sp.current_playback()

        if not playback or not playback["item"]:
            return None

        track = playback["item"]

        return {
            "name": track["name"],
            "artists": [artist["name"] for artist in track["artists"]],
            "album": track["album"]["name"],
            "uri": track["uri"]
        }


    def get_playlist(self):
        data = request.json
        playlist_id = data.get('playlist_id')
        return self.sp.playlist(playlist_id)


    def get_playlist_tracks(self):
        data = request.json
        playlist_id = data.get('playlist_id')
        tracks = self.sp.playlist_tracks(playlist_id)
        songs = []

        while tracks:
            for item in tracks["items"]:
                track = item["track"]

                if track:
                    songs.append({
                        "name": track["name"],
                        "artists": [artist["name"] for artist in track["artists"]],
                        "uri": track["uri"]
                    })

            if not tracks["next"]:
                break

            tracks = self.sp.next(tracks)

        return songs


    def play(self):
        self.sp.start_playback()


    def pause(self):
        self.sp.pause_playback()


    def next(self):
        self.sp.next_track()


    def previous(self):
        self.sp.previous_track()
