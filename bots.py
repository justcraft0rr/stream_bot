import requests
import asyncio
import os
import re
import json
from datetime import datetime
from twitchio.ext import commands, eventsub
from flask import request
from openai import OpenAI
from spotipy.oauth2 import SpotifyOAuth
from threading import Thread
import pytchat
import obsws_python
import spotipy
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
class TwithBot(commands.Bot):
    def __init__(self, **kwargs):
        self.requirements = {
            'twitch_refresh_token': kwargs.get('twitch_refresh_token'),
            'twitch_token_id': kwargs.get('twitch_token_id'),
            'twitch_token_secret': kwargs.get('twitch_token_secret'),
            'twitch_broadcaster': kwargs.get('twitch_broadcaster'),
            'twitch_bot': kwargs.get('twitch_bot'),
            'stream_events': kwargs.get('stream_events'),
            'flask': kwargs.get('flask')
        }
        self.twitch_token = self.refresh_twitch_token(
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
        self.stream_events = self.requirements['stream_events']
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
        broadcaster = (await self.fetch_users(
            names=[self.requirements['twitch_broadcaster']]
        ))[0].id
        moderator = (await self.fetch_users(
            names=[self.requirements['twitch_bot']]
        ))[0].id
        await self.eventsub.subscribe_channel_follows_v2(
            broadcaster=broadcaster,
            moderator=moderator,
            token=self.twitch_token
        )
        asyncio.create_task(self.live_handle())
        print('Twitch Connected!')
    
    async def event_eventsub_notification_followV2(
        self,
        event: eventsub.ChannelFollowData
    ):
        self.stream_events.append({'event': 'follow', 'platform': 'twitch', 'username': event.user.name})
    
    async def event_message(self, message):
        self.stream_events.append({'event': 'message', 'platform': 'twitch', 'username': message.author.name, 'message': message.content})
        print(f'[Twitch] {message.author.name}: {message.content}')
    
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
                    self.stream_events['stream_id'] = 0
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

class KickBot:

    def __init__(self, **kwargs):

        self.requirements = {
            'kick_client_id': kwargs.get('kick_client_id'),
            'kick_client_secret': kwargs.get('kick_client_secret'),
            'kick_broadcaster': kwargs.get('kick_broadcaster'),
            'kick_webhook_url': kwargs.get('kick_webhook_url'),
            'stream_events': kwargs.get('stream_events'),
            'flask': kwargs.get('flask')
        }

        self.access_token = os.getenv('kick_access_token')
        self.refresh_token = os.getenv('kick_refresh_token')

        self.ready = False
        self.stream_events = self.requirements['stream_events']
        self.connector = '≋'

        self.flask = self.requirements['flask']

        self.flask.add_url_rule(
            '/kick/status',
            'kick_status',
            self.status
        )

        self.flask.add_url_rule(
            '/kick/user/<username>',
            'kick_user',
            self.flask_user
        )

        self.flask.add_url_rule(
            '/kick/channel',
            'kick_channel',
            self.flask_channel
        )

        self.flask.add_url_rule(
            '/kick/stream-info',
            'kick_stream_info',
            self.stream
        )

        self.flask.add_url_rule(
            '/kick/events',
            'kick_events',
            self.events
        )

        self.flask.add_url_rule(
            '/kick/send_message',
            'kick_send_message',
            self.flask_send_message,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/delete_message',
            'kick_delete_message',
            self.flask_delete_message,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/ban',
            'kick_ban',
            self.flask_ban,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/unban',
            'kick_unban',
            self.flask_unban,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/timeout',
            'kick_timeout',
            self.flask_timeout,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/update_channel',
            'kick_update_channel',
            self.flask_update_channel,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/rewards',
            'kick_rewards',
            self.flask_rewards
        )

        self.flask.add_url_rule(
            '/kick/rewards/create',
            'kick_rewards_create',
            self.flask_rewards_create,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/rewards/<reward_id>',
            'kick_rewards_update',
            self.flask_rewards_update,
            methods=['PATCH']
        )

        self.flask.add_url_rule(
            '/kick/rewards/<reward_id>/delete',
            'kick_rewards_delete',
            self.flask_rewards_delete,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/redemptions',
            'kick_redemptions',
            self.flask_redemptions
        )

        self.flask.add_url_rule(
            '/kick/redemptions/accept',
            'kick_redemptions_accept',
            self.flask_redemptions_accept,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/redemptions/reject',
            'kick_redemptions_reject',
            self.flask_redemptions_reject,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/kick/kicks/leaderboard',
            'kick_kicks_leaderboard',
            self.flask_kicks_leaderboard
        )

        self.flask.add_url_rule(
            '/kick/subscriptions',
            'kick_subscriptions',
            self.flask_subscriptions
        )

        self.flask.add_url_rule(
            '/kick/webhook',
            'kick_webhook',
            self.webhook,
            methods=['POST']
        )

        self.broadcaster = self.get_user(
            self.requirements['kick_broadcaster']
        )

        if self.broadcaster:

            self.broadcaster_id = self.broadcaster.get('user_id')

            if not self.broadcaster_id:
                self.broadcaster_id = self.broadcaster.get('id')

            self.ready = True

    def request(self, method, endpoint, **kwargs):

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.request(
            method,
            f'https://api.kick.com/public/v1/{endpoint}',
            headers=headers,
            **kwargs
        )

        if response.status_code == 401:

            if self.refresh():

                headers['Authorization'] = (
                    f'Bearer {self.access_token}'
                )

                response = requests.request(
                    method,
                    f'https://api.kick.com/public/v1/{endpoint}',
                    headers=headers,
                    **kwargs
                )

        return response

    def refresh(self):

        if not self.refresh_token:
            return False

        response = requests.post(
            'https://id.kick.com/oauth/token',
            data={
                'grant_type': 'refresh_token',
                'client_id': self.requirements['kick_client_id'],
                'client_secret': self.requirements['kick_client_secret'],
                'refresh_token': self.refresh_token
            }
        )

        if not response.ok:
            return False

        tokens = response.json()

        self.access_token = tokens['access_token']
        self.refresh_token = tokens['refresh_token']

        self.save_tokens()

        return True

    def save_tokens(self):

        bashrc = os.path.expanduser('~/.bashrc')

        with open(bashrc, 'r') as file:
            lines = file.read().splitlines()

        lines = [
            line for line in lines
            if not line.startswith('export kick_access_token=')
            and not line.startswith('export kick_refresh_token=')
        ]

        lines.append(
            f'export kick_access_token="{self.access_token}"'
        )

        lines.append(
            f'export kick_refresh_token="{self.refresh_token}"'
        )

        with open(bashrc, 'w') as file:
            file.write('\n'.join(lines) + '\n')

    def get_user(self, username=None):

        params = {}

        if username:
            params['username'] = username

        response = self.request(
            'GET',
            'users',
            params=params
        )

        if not response.ok:
            return None

        data = response.json().get('data')

        if not data:
            return None

        return data[0]

    def get_channel(self):

        response = self.request(
            'GET',
            'channels',
            params={
                'broadcaster_user_id': self.broadcaster_id
            }
        )

        if not response.ok:
            return None

        data = response.json().get('data')

        if not data:
            return None

        return data[0]

    def get_stream(self):

        response = self.request(
            'GET',
            'livestreams',
            params={
                'broadcaster_user_id': self.broadcaster_id
            }
        )

        if not response.ok:
            return None

        data = response.json().get('data')

        if not data:
            return None

        return data[0]

    def is_live(self):

        return self.get_stream() is not None

    def send_message(self, message, reply_to_message_id=None):

        data = {
            'broadcaster_user_id': self.broadcaster_id,
            'content': message,
            'type': 'bot'
        }

        if reply_to_message_id:
            data['reply_to_message_id'] = reply_to_message_id

        response = self.request(
            'POST',
            'chat',
            json=data
        )

        if not response.ok:
            return False

        return response.json()

    def delete_message(self, message_id):

        response = self.request(
            'DELETE',
            f'chat/{message_id}'
        )

        return response.ok

    def ban(self, user_id, reason=None):

        data = {
            'broadcaster_user_id': self.broadcaster_id,
            'user_id': user_id
        }

        if reason:
            data['reason'] = reason

        response = self.request(
            'POST',
            'moderation/bans',
            json=data
        )

        return response.ok

    def timeout(self, user_id, duration, reason=None):

        data = {
            'broadcaster_user_id': self.broadcaster_id,
            'user_id': user_id,
            'duration': duration
        }

        if reason:
            data['reason'] = reason

        response = self.request(
            'POST',
            'moderation/bans',
            json=data
        )

        return response.ok

    def unban(self, user_id):

        response = self.request(
            'DELETE',
            'moderation/bans',
            json={
                'broadcaster_user_id': self.broadcaster_id,
                'user_id': user_id
            }
        )

        return response.ok

    def update_channel(self, **kwargs):

        data = {}

        if kwargs.get('category_id') is not None:
            data['category_id'] = kwargs.get('category_id')

        if kwargs.get('title') is not None:
            data['title'] = kwargs.get('title')

        if kwargs.get('language') is not None:
            data['language'] = kwargs.get('language')

        if kwargs.get('custom_tags') is not None:
            data['custom_tags'] = kwargs.get('custom_tags')

        response = self.request(
            'PATCH',
            'channels',
            json=data
        )

        return response.ok

    def get_rewards(self):

        response = self.request(
            'GET',
            'channels/rewards'
        )

        if not response.ok:
            return None

        return response.json()

    def create_reward(
        self,
        title,
        cost,
        description=None,
        is_user_input_required=False,
        is_enabled=True,
        is_paused=False,
        is_in_stock=True
    ):

        data = {
            'title': title,
            'cost': cost,
            'is_user_input_required': is_user_input_required,
            'is_enabled': is_enabled,
            'is_paused': is_paused,
            'is_in_stock': is_in_stock
        }

        if description is not None:
            data['description'] = description

        response = self.request(
            'POST',
            'channels/rewards',
            json=data
        )

        if not response.ok:
            return None

        return response.json()

    def update_reward(self, reward_id, **kwargs):

        data = {}

        allowed = [
            'title',
            'cost',
            'description',
            'is_user_input_required',
            'is_enabled',
            'is_paused',
            'is_in_stock'
        ]

        for key in allowed:

            if key in kwargs:
                data[key] = kwargs[key]

        response = self.request(
            'PATCH',
            f'channels/rewards/{reward_id}',
            json=data
        )

        return response.ok

    def delete_reward(self, reward_id):

        response = self.request(
            'DELETE',
            f'channels/rewards/{reward_id}'
        )

        return response.ok

    def get_redemptions(self, **kwargs):

        response = self.request(
            'GET',
            'channels/rewards/redemptions',
            params=kwargs
        )

        if not response.ok:
            return None

        return response.json()

    def accept_redemptions(self, redemption_ids):

        response = self.request(
            'POST',
            'channels/rewards/redemptions/accept',
            json={
                'ids': redemption_ids
            }
        )

        return response.ok

    def reject_redemptions(self, redemption_ids):

        response = self.request(
            'POST',
            'channels/rewards/redemptions/reject',
            json={
                'ids': redemption_ids
            }
        )

        return response.ok

    def get_kicks_leaderboard(self, **kwargs):

        response = self.request(
            'GET',
            'kicks/leaderboard',
            params=kwargs
        )

        if not response.ok:
            return None

        return response.json()

    def get_subscriptions(self):

        response = self.request(
            'GET',
            'channels',
            params={
                'broadcaster_user_id': self.broadcaster_id
            }
        )

        if not response.ok:
            return None

        return response.json()

    def subscribe_events(self):

        events = [
            'chat.message.sent',
            'channel.followed',
            'channel.subscription.new',
            'channel.subscription.renewal',
            'channel.subscription.gifts',
            'channel.reward.redemption.updated',
            'livestream.status.updated',
            'livestream.metadata.updated',
            'moderation.banned',
            'kicks.gifted'
        ]

        results = []

        for event in events:

            response = self.request(
                'POST',
                'events/subscriptions',
                json={
                    'broadcaster_user_id': self.broadcaster_id,
                    'events': [
                        {
                            'name': event,
                            'version': 1
                        }
                    ],
                    'method': 'webhook'
                }
            )

            results.append({
                'event': event,
                'success': response.ok,
                'status': response.status_code
            })

        return results

    def get_event_subscriptions(self):

        response = self.request(
            'GET',
            'events/subscriptions'
        )

        if not response.ok:
            return None

        return response.json()

    def delete_event_subscriptions(self, **kwargs):

        response = self.request(
            'DELETE',
            'events/subscriptions',
            json=kwargs
        )

        return response.ok

    def webhook(self):

        event_type = request.headers.get('Kick-Event-Type')
        event = request.get_json(silent=True) or {}

        if event_type == 'chat.message.sent':

            sender = event.get('sender', {})

            self.stream_events.append({
                'event': 'message',
                'platform': 'kick',
                'username': sender.get('username'),
                'user_id': sender.get('user_id'),
                'message': event.get('content'),
                'message_id': event.get('message_id')
            })

        elif event_type == 'channel.followed':

            follower = event.get('follower', {})

            self.stream_events.append({
                'event': 'follow',
                'platform': 'kick',
                'username': follower.get('username'),
                'user_id': follower.get('user_id')
            })

        elif event_type == 'channel.subscription.new':

            subscriber = event.get('subscriber', {})

            self.stream_events.append({
                'event': 'subscription',
                'platform': 'kick',
                'username': subscriber.get('username'),
                'user_id': subscriber.get('user_id'),
                'duration': event.get('duration')
            })

        elif event_type == 'channel.subscription.renewal':

            subscriber = event.get('subscriber', {})

            self.stream_events.append({
                'event': 'subscription_renewal',
                'platform': 'kick',
                'username': subscriber.get('username'),
                'user_id': subscriber.get('user_id'),
                'duration': event.get('duration')
            })

        elif event_type == 'channel.subscription.gifts':

            gifter = event.get('gifter', {})

            self.stream_events.append({
                'event': 'subscription_gift',
                'platform': 'kick',
                'username': gifter.get('username'),
                'user_id': gifter.get('user_id'),
                'giftees': event.get('giftees', [])
            })

        elif event_type == 'channel.reward.redemption.updated':

            redeemer = event.get('redeemer', {})

            self.stream_events.append({
                'event': 'reward_redemption',
                'platform': 'kick',
                'username': redeemer.get('username'),
                'user_id': redeemer.get('user_id'),
                'reward': event.get('reward'),
                'status': event.get('status'),
                'user_input': event.get('user_input')
            })

        elif event_type == 'livestream.status.updated':

            self.stream_events.append({
                'event': 'live',
                'platform': 'kick',
                'live': event.get('is_live'),
                'title': event.get('title'),
                'started_at': event.get('started_at'),
                'ended_at': event.get('ended_at')
            })

        elif event_type == 'livestream.metadata.updated':

            metadata = event.get('metadata', {})

            self.stream_events.append({
                'event': 'stream_metadata',
                'platform': 'kick',
                'title': metadata.get('title'),
                'language': metadata.get('language'),
                'has_mature_content': metadata.get('has_mature_content'),
                'category': metadata.get('category')
            })

        elif event_type == 'moderation.banned':

            banned_user = event.get('banned_user', {})
            metadata = event.get('metadata', {})

            self.stream_events.append({
                'event': 'ban',
                'platform': 'kick',
                'username': banned_user.get('username'),
                'user_id': banned_user.get('user_id'),
                'reason': metadata.get('reason'),
                'expires_at': metadata.get('expires_at')
            })

        elif event_type == 'kicks.gifted':

            sender = event.get('sender', {})
            gift = event.get('gift', {})

            self.stream_events.append({
                'event': 'kicks',
                'platform': 'kick',
                'username': sender.get('username'),
                'user_id': sender.get('user_id'),
                'amount': gift.get('amount'),
                'name': gift.get('name'),
                'type': gift.get('type'),
                'tier': gift.get('tier'),
                'message': gift.get('message')
            })

        return '', 200

    def events(self):

        return self.stream_events

    def stream(self):

        stream = self.get_stream()

        if not stream:
            return {
                'live': False
            }

        return stream

    def status(self):

        return {
            'ready': self.ready,
            'live': self.is_live()
        }

    def flask_user(self, username):

        user = self.get_user(username)

        if not user:
            return {
                'error': 'User not found'
            }, 404

        return user

    def flask_channel(self):

        channel = self.get_channel()

        if not channel:
            return {
                'error': 'Channel not found'
            }, 404

        return channel

    def flask_send_message(self):

        data = request.get_json() or {}

        if not data.get('message'):
            return {
                'error': 'Missing message'
            }, 400

        result = self.send_message(
            data['message'],
            data.get('reply_to_message_id')
        )

        if not result:
            return {
                'error': 'Failed to send message'
            }, 500

        return result

    def flask_delete_message(self):

        data = request.get_json() or {}

        if not data.get('message_id'):
            return {
                'error': 'Missing message_id'
            }, 400

        return {
            'success': self.delete_message(
                data['message_id']
            )
        }

    def flask_ban(self):

        data = request.get_json() or {}

        if not data.get('user_id'):
            return {
                'error': 'Missing user_id'
            }, 400

        return {
            'success': self.ban(
                data['user_id'],
                data.get('reason')
            )
        }

    def flask_unban(self):

        data = request.get_json() or {}

        if not data.get('user_id'):
            return {
                'error': 'Missing user_id'
            }, 400

        return {
            'success': self.unban(
                data['user_id']
            )
        }

    def flask_timeout(self):

        data = request.get_json() or {}

        if not data.get('user_id'):
            return {
                'error': 'Missing user_id'
            }, 400

        if not data.get('duration'):
            return {
                'error': 'Missing duration'
            }, 400

        return {
            'success': self.timeout(
                data['user_id'],
                data['duration'],
                data.get('reason')
            )
        }

    def flask_update_channel(self):

        data = request.get_json() or {}

        return {
            'success': self.update_channel(**data)
        }

    def flask_rewards(self):

        rewards = self.get_rewards()

        if rewards is None:
            return {
                'error': 'Failed to get rewards'
            }, 500

        return rewards

    def flask_rewards_create(self):

        data = request.get_json() or {}

        if not data.get('title'):
            return {
                'error': 'Missing title'
            }, 400

        if data.get('cost') is None:
            return {
                'error': 'Missing cost'
            }, 400

        result = self.create_reward(
            title=data['title'],
            cost=data['cost'],
            description=data.get('description'),
            is_user_input_required=data.get(
                'is_user_input_required',
                False
            ),
            is_enabled=data.get(
                'is_enabled',
                True
            ),
            is_paused=data.get(
                'is_paused',
                False
            ),
            is_in_stock=data.get(
                'is_in_stock',
                True
            )
        )

        if result is None:
            return {
                'error': 'Failed to create reward'
            }, 500

        return result

    def flask_rewards_update(self, reward_id):

        data = request.get_json() or {}

        return {
            'success': self.update_reward(
                reward_id,
                **data
            )
        }

    def flask_rewards_delete(self, reward_id):

        return {
            'success': self.delete_reward(
                reward_id
            )
        }

    def flask_redemptions(self):

        data = request.args.to_dict()

        result = self.get_redemptions(**data)

        if result is None:
            return {
                'error': 'Failed to get redemptions'
            }, 500

        return result

    def flask_redemptions_accept(self):

        data = request.get_json() or {}

        if not data.get('ids'):
            return {
                'error': 'Missing ids'
            }, 400

        return {
            'success': self.accept_redemptions(
                data['ids']
            )
        }

    def flask_redemptions_reject(self):

        data = request.get_json() or {}

        if not data.get('ids'):
            return {
                'error': 'Missing ids'
            }, 400

        return {
            'success': self.reject_redemptions(
                data['ids']
            )
        }

    def flask_kicks_leaderboard(self):

        result = self.get_kicks_leaderboard(
            **request.args.to_dict()
        )

        if result is None:
            return {
                'error': 'Failed to get leaderboard'
            }, 500

        return result

    def flask_subscriptions(self):

        result = self.get_subscriptions()

        if result is None:
            return {
                'error': 'Failed to get subscriptions'
            }, 500

        return result

class YoutubeBot:
    def __init__(self, **kwargs):
        self.requirements = {
            'youtube_channel': kwargs.get('youtube_channel'),
            'stream_events': kwargs.get('stream_events'),
            'flask': kwargs.get('flask')
        }
        if self.get_stream():
            self.chat = pytchat.create(
                video_id=self.get_stream()
            )
        else:
            self.chat = None
        Thread(
            target=lambda: asyncio.run(self.live_handle()),
            daemon=True
        ).start()
        self.stream_events = self.requirements['stream_events']
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
        while self.chat and self.chat.is_alive():
            for message in self.chat.get().sync_items():
                self.stream_events.append({
                    'event': 'message',
                    'platform': 'youtube',
                    'username': message.author.name,
                    'message': message.message
                })

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
    
    def ask(self):
        data = request.json
        prompt = data.get('prompt')
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
            scope='user-read-playback-state user-modify-playback-state playlist-read-private'
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
            self.get_playlist,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/spotify/get/playlist_tracks',
            'get_playlist_tracks',
            self.get_playlist_tracks,
            methods=['POST']
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
            '/spotify/play/song',
            'play_song',
            self.play_song,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/spotify/play/playlist',
            'play_playlist',
            self.play_playlist,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/spotify/get/devices',
            'get_devices',
            self.get_devices
        )

        self.flask.add_url_rule(
            '/spotify/change_device',
            'change_device',
            self.change_device,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/spotify/change_device_by_name',
            'change_device_by_name',
            self.change_device_by_name,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/spotify/search/song',
            'search_song',
            self.search_song,
            methods=['POST']
        )

        self.flask.add_url_rule(
            '/spotify/queue/add_song',
            'add_song_to_queue',
            self.add_to_queue,
            methods=['POST']
        )

    def add_to_queue(self):
        data = request.json
        track_uri = data.get('track_uri')
        device_id = data.get('device_id')

        self.sp.add_to_queue(
            uri=track_uri,
            device_id=device_id
        )

    def search_song(self):
        data = request.json
        query = data.get('query')

        results = self.sp.search(
            q=query,
            type='track',
            limit=1
        )

        if not results['tracks']['items']:
            return None

        return results['tracks']['items'][0]

    def play_song(self):
        data = request.json
        track_uri = data.get('track_uri')
        device_id = data.get('device_id')

        self.sp.start_playback(
            device_id=device_id,
            uris=[track_uri]
        )

    def play_playlist(self):
        data = request.json
        playlist_id = data.get('playlist_id')
        device_id = data.get('device_id')

        self.sp.start_playback(
            device_id=device_id,
            context_uri=f'spotify:playlist:{playlist_id}'
        )

    def get_devices(self):
        return self.sp.devices()['devices']

    def change_device(self):
        data = request.json
        device_id = data.get('device_id')
        play = data.get('play', False)

        self.sp.transfer_playback(
            device_id=device_id,
            force_play=play
        )

    def change_device_by_name(self):
        data = request.json
        name = data.get('name')
        play = data.get('play', False)

        devices = self.get_devices()

        for device in devices:
            if device['name'].lower() == name.lower():
                self.sp.transfer_playback(
                    device_id=device['id'],
                    force_play=play
                )
                return device

        return None

    def current_song(self):
        playback = self.sp.current_playback()

        if not playback or not playback['item']:
            return None

        track = playback['item']

        return {
            'name': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'album': track['album']['name'],
            'uri': track['uri']
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
            for item in tracks['items']:
                track = item['track']

                if track:
                    songs.append({
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'uri': track['uri']
                    })

            if not tracks['next']:
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
