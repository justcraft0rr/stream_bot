import requests

class FlaskClient:

    def __init__(self, **kwargs):

        self.requirements = {
            'flask_host_ip': kwargs.get('flask_host_ip'),
            'flask_host_port': kwargs.get('flask_host_port')
        }

        self.Twitch = self.twitch(self)
        self.Kick = self.kick(self)
        self.Youtube = self.youtube(self)
        self.OBS = self.obs(self)
        self.GPT = self.gpt(self)
        self.Spotify = self.spotify(self)

    def get(self, endpoint, **kwargs):

        return requests.get(
            f"http://{self.requirements['flask_host_ip']}:"
            f"{self.requirements['flask_host_port']}{endpoint}",
            **kwargs
        ).json()

    def post(self, endpoint, **kwargs):

        return requests.post(
            f"http://{self.requirements['flask_host_ip']}:"
            f"{self.requirements['flask_host_port']}{endpoint}",
            **kwargs
        ).json()

    def patch(self, endpoint, **kwargs):

        return requests.patch(
            f"http://{self.requirements['flask_host_ip']}:"
            f"{self.requirements['flask_host_port']}{endpoint}",
            **kwargs
        ).json()

    def delete(self, endpoint, **kwargs):

        return requests.delete(
            f"http://{self.requirements['flask_host_ip']}:"
            f"{self.requirements['flask_host_port']}{endpoint}",
            **kwargs
        ).json()

    class twitch:

        def __init__(self, client):
            self.client = client

        def stream_info(self):
            return self.client.get('/twitch/stream-info')

        def status(self):
            return self.client.get('/twitch/status')

        def start(self):
            return self.client.get('/twitch/start')

        def stop(self):
            return self.client.post('/twitch/stop')

        def reload(self):
            return self.client.post('/twitch/reload')

        def user_info(self, user):
            return self.client.get(f'/twitch/user/{user}')

        def events(self):
            return self.client.get('/twitch/events')

        def send_message(self, message):
            return self.client.post(
                '/twitch/send_message',
                json={'message': message}
            )

        def ban(self, user, reason):
            return self.client.post(
                '/twitch/ban',
                json={
                    'username': user,
                    'reason': reason
                }
            )

        def unban(self, user):
            return self.client.post(
                '/twitch/unban',
                json={
                    'username': user
                }
            )

        def timeout(self, user, duration, reason):
            return self.client.post(
                '/twitch/timeout',
                json={
                    'username': user,
                    'duration': duration,
                    'reason': reason
                }
            )

        def create_clip(self):
            return self.client.post('/twitch/create-clip')

        def add_moderator(self, user):
            return self.client.post(
                '/twitch/add-moderator',
                json={'username': user}
            )

        def remove_moderator(self, user):
            return self.client.post(
                '/twitch/remove-moderator',
                json={'username': user}
            )

        def add_vip(self, user):
            return self.client.post(
                '/twitch/add-vip',
                json={'username': user}
            )

        def remove_vip(self, user):
            return self.client.post(
                '/twitch/remove-vip',
                json={'username': user}
            )

    class kick:

        def __init__(self, client):
            self.client = client

        def status(self):
            return self.client.get('/kick/status')

        def user_info(self, user):
            return self.client.get(f'/kick/user/{user}')

        def channel(self):
            return self.client.get('/kick/channel')

        def stream_info(self):
            return self.client.get('/kick/stream-info')

        def events(self):
            return self.client.get('/kick/events')

        def send_message(self, message):
            return self.client.post(
                '/kick/send_message',
                json={'message': message}
            )

        def delete_message(self, message_id):
            return self.client.post(
                '/kick/delete_message',
                json={'message_id': message_id}
            )

        def ban(self, user, reason=None):
            data = {'username': user}

            if reason is not None:
                data['reason'] = reason

            return self.client.post(
                '/kick/ban',
                json=data
            )

        def unban(self, user):
            return self.client.post(
                '/kick/unban',
                json={'username': user}
            )

        def timeout(self, user, duration, reason=None):
            data = {
                'username': user,
                'duration': duration
            }

            if reason is not None:
                data['reason'] = reason

            return self.client.post(
                '/kick/timeout',
                json=data
            )

        def update_channel(self, **kwargs):
            return self.client.post(
                '/kick/update_channel',
                json=kwargs
            )

        def rewards(self):
            return self.client.get('/kick/rewards')

        def create_reward(self, **kwargs):
            return self.client.post(
                '/kick/rewards/create',
                json=kwargs
            )

        def update_reward(self, reward_id, **kwargs):
            return self.client.patch(
                f'/kick/rewards/{reward_id}',
                json=kwargs
            )

        def delete_reward(self, reward_id):
            return self.client.post(
                f'/kick/rewards/{reward_id}/delete'
            )

        def redemptions(self, **kwargs):
            return self.client.get(
                '/kick/redemptions',
                params=kwargs
            )

        def accept_redemptions(self, **kwargs):
            return self.client.post(
                '/kick/redemptions/accept',
                json=kwargs
            )

        def reject_redemptions(self, **kwargs):
            return self.client.post(
                '/kick/redemptions/reject',
                json=kwargs
            )

        def kicks_leaderboard(self, **kwargs):
            return self.client.get(
                '/kick/kicks/leaderboard',
                params=kwargs
            )

        def subscriptions(self, **kwargs):
            return self.client.get(
                '/kick/subscriptions',
                params=kwargs
            )

    class youtube:

        def __init__(self, client):
            self.client = client

    class obs:

        def __init__(self, client):
            self.client = client

        def scenes(self):
            return self.client.get('/obs/get/scenes')

        def program_scene(self):
            return self.client.get('/obs/get/program_scene')

        def set_program_scene(self, scene):
            return self.client.post(
                '/obs/set/program_scene',
                json={'scene': scene}
            )

        def scene_item_list(self, scene_name):
            return self.client.get(
                '/obs/get/scene_item_list',
                params={'scene_name': scene_name}
            )

        def scene_item_id(self, scene_name, source_name):
            return self.client.get(
                '/obs/get/scene_item_id',
                params={
                    'scene_name': scene_name,
                    'source_name': source_name
                }
            )

    class gpt:

        def __init__(self, client):
            self.client = client

        def ask(self, prompt):
            return self.client.post(
                '/gpt/ask',
                json={'prompt': prompt}
            )

    class spotify:

        def __init__(self, client):
            self.client = client

        def current_song(self):
            return self.client.get('/spotify/get/current_song')

        def playlist(self, playlist_id):
            return self.client.post(
                '/spotify/get/playlist',
                json={'playlist_id': playlist_id}
            )

        def playlist_tracks(self, playlist_id):
            return self.client.post(
                '/spotify/get/playlist_tracks',
                json={'playlist_id': playlist_id}
            )

        def play(self):
            return self.client.get('/spotify/mediacontrol/play')

        def pause(self):
            return self.client.get('/spotify/mediacontrol/pause')

        def next(self):
            return self.client.get('/spotify/mediacontrol/next')

        def previous(self):
            return self.client.get('/spotify/mediacontrol/previous')

        def play_song(self, track_uri, device_id=None):
            return self.client.post(
                '/spotify/play/song',
                json={
                    'track_uri': track_uri,
                    'device_id': device_id
                }
            )

        def play_playlist(self, playlist_id, device_id=None):
            return self.client.post(
                '/spotify/play/playlist',
                json={
                    'playlist_id': playlist_id,
                    'device_id': device_id
                }
            )

        def devices(self):
            return self.client.get('/spotify/get/devices')

        def change_device(self, device_id, play=False):
            return self.client.post(
                '/spotify/change_device',
                json={
                    'device_id': device_id,
                    'play': play
                }
            )

        def change_device_by_name(self, name, play=False):
            return self.client.post(
                '/spotify/change_device_by_name',
                json={
                    'name': name,
                    'play': play
                }
            )

        def search_song(self, query):
            return self.client.post(
                '/spotify/search/song',
                json={'query': query}
            )

        def add_to_queue(self, track_uri, device_id=None):
            return self.client.post(
                '/spotify/queue/add_song',
                json={
                    'track_uri': track_uri,
                    'device_id': device_id
                }
            )
