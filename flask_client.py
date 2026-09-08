import requests
class FlaskClient:
    def __init__(self, **kwargs):
        self.requirements = {
            'flask_host_ip': kwargs.get('flask_host_ip'),
            'flask_host_port': kwargs.get('flask_host_port')
        }
        self.Twitch = self.twitch(self)
        self.Youtube = self.youtube(self)
    
    def get(self, endpoint):
        return requests.get(
            f"http://{self.requirements['flask_host_ip']}:{self.requirements['flask_host_port']}{endpoint}"
        ).json()

    def post(self, endpoint, **kwargs):
        return requests.post(
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
                json={
                    'username': user
                }
            )
        
        def remove_moderator(self, user):
            return self.client.post(
                '/twitch/remove-moderator',
                json={
                    'username': user
                }
            )
        
        def add_vip(self, user):
            return self.client.post(
                '/twitch/add-vip',
                json={
                    'username': user
                }
            )
        
        def remove_vip(self, user):
            return self.client.post(
                '/twitch/remove-vip',
                json={
                    'username': user
                }
            )
    
    class youtube:
        def __init__(self, client):
            self.client = client
