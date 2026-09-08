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
        def __init__(self, the_self):
            self = the_self
    
    class youtube:
        def __init__(self, the_self):
            self = the_self

