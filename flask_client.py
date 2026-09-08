import requests
class FlaskClient:
    def __init__(self, **kwargs):
        self.requirements = {
            'flask_host_ip': kwargs.get('flask_host_ip'),
            'flask_host_port': kwargs.get('flask_host_port')
        }
