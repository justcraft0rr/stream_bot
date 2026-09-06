import requests
import asyncio
import os
import re
import json
from datetime import datetime
from twitchio.ext import commands, eventsub
class TwithBot(commands.Bot):
    def __init__(self, **kwargs):
        self.requirements = {
            'twitch_refresh_token': kwargs.get('twitch_refresh_token'),
            'twitch_token_id': kwargs.get('twitch_token_id'),
            'twitch_token_secret': kwargs.get('twitch_token_secret'),
            'twitch_broadcaster': kwargs.get('twitch_broadcaster'),
            'twitch_bot': kwargs.get('twitch_bot')
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
    
    def run(self):
        super().run()
    
    def refresh_twitch_token(self, client_id, client_secret, refresh_token):
        if not client_id or not client_secret or not refresh_token:
            raise RuntimeError(
                "Missing twitch_client_id, twitch_client_secret, or twitch_refresh_token"
            )

        response = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

        response.raise_for_status()
        data = response.json()

        access_token = data["access_token"]
        new_refresh_token = data.get("refresh_token", refresh_token)

        # Read .bashrc
        bashrc = os.path.expanduser("~/.bashrc")

        with open(bashrc, "r") as f:
            content = f.read()

        # Update ONLY the token variables
        content = re.sub(
            r"^export twitch_token=.*$",
            f'export twitch_token="{access_token}"',
            content,
            flags=re.MULTILINE,
        )

        content = re.sub(
            r"^export twitch_refresh_token=.*$",
            f'export twitch_refresh_token="{new_refresh_token}"',
            content,
            flags=re.MULTILINE,
        )

        # Write .bashrc back
        with open(bashrc, "w") as f:
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
