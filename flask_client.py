import requests
class FlaskClient:
    def __init__(self, **kwargs):
        self.requirements = {
            'flask_host_ip': kwargs.get('flask_host_ip'),
            'flask_host_port': kwargs.get('flask_host_port')
        }
        self.Twitch = self.twitch(self.requirements)
        self.Youtube = self.youtube(self.requirements)
    
    class twitch:
        def __init__(self, info):
            self.requirements = info
    
    class youtube:
        def __init__(self, info):
            self.requirements = info

