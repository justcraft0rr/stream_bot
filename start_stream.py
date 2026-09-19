from start_bots import start_bots
from flask import Flask
from os import getenv
from html import escape
import tomllib
config = tomllib.load(open('/home/justcraft/config.toml', 'rb'))
flask = Flask(__name__)
stream_events = []
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
@flask.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Stream Bot</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 40px;
            background: #0b0b0f;
            color: #eee;
            font-family: Arial, sans-serif;
        }

        h1 {
            margin: 0 0 35px;
        }

        .dashboard {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            border-top: 1px solid #292932;
            border-left: 1px solid #292932;
        }

        .item {
            min-height: 150px;
            padding: 25px;
            border-right: 1px solid #292932;
            border-bottom: 1px solid #292932;
        }

        .label {
            color: #777;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }

        .value {
            font-size: 25px;
            font-weight: bold;
        }

        .online {
            color: #45e68a;
        }

        .events {
            grid-column: span 2;
        }

        .event {
            padding: 8px 0;
            border-bottom: 1px solid #202028;
        }

        .event:last-child {
            border-bottom: none;
        }

        .time {
            color: #666;
            margin-right: 15px;
        }

        button {
            background: transparent;
            color: #eee;
            border: 1px solid #33333d;
            padding: 9px 15px;
            border-radius: 6px;
            cursor: pointer;
            margin-right: 8px;
        }

        button:hover {
            background: #191920;
        }

        @media (max-width: 800px) {
            .dashboard {
                grid-template-columns: 1fr;
            }

            .events {
                grid-column: span 1;
            }
        }
    </style>
</head>

<body>

    <h1>Stream Bot</h1>

    <div class='dashboard'>

        <div class='item'>
            <div class='label'>Status</div>
            <div class='value online'>● LIVE</div>
        </div>

        <div class='item'>
            <div class='label'>Viewers</div>
            <div class='value'>42</div>
        </div>

        <div class='item'>
            <div class='label'>Uptime</div>
            <div class='value'>01:24:37</div>
        </div>


        <div class='item'>
            <div class='label'>Twitch</div>
            <div class='value online'>Connected</div>
        </div>

        <div class='item'>
            <div class='label'>YouTube</div>
            <div class='value online'>Connected</div>
        </div>

        <div class='item'>
            <div class='label'>OBS</div>
            <div class='value online'>Connected</div>
        </div>


        <div class='item events'>
            <div class='label'>Recent Events</div>

            <div class='event'>
                <span class='time'>12:41</span>
                viewer123 followed
            </div>

            <div class='event'>
                <span class='time'>12:40</span>
                cool_user sent a message
            </div>

            <div class='event'>
                <span class='time'>12:38</span>
                Stream started
            </div>
        </div>

        <div class='item'>
            <div class='label'>Bot</div>
            <div class='value online'>Running</div>
        </div>


        <div class='item'>
            <div class='label'>Controls</div>

            <button>Refresh</button>
            <button>Reload</button>
        </div>

        <div class='item'>
            <div class='label'>Spotify</div>
            <div class='value online'>Connected</div>
        </div>

        <div class='item'>
            <div class='label'>ElevenLabs</div>
            <div class='value online'>Ready</div>
        </div>

    </div>

    <script>
    async function updateDashboard() {
        try {
            const response = await fetch('/api/main');
            const data = await response.json();

            document.getElementById('status').textContent = '● ' + data.status;
            document.getElementById('viewers').textContent = data.viewers;
            document.getElementById('uptime').textContent = data.uptime;

        } catch (error) {
            console.error('Dashboard update failed:', error);
        }
    }

    updateDashboard();

    setInterval(updateDashboard, 1000);
    </script>
</body>
</html>
'''
@flask.route('/chat/api/<platform>')
def chat_api(platform):
    if platform not in ['all', 'twitch', 'youtube', 'kick']:
        return {'error': 'Wrong API Platform'}, 404
@flask.route('/chat/<platform>')
def chat(platform):
    platform = platform.lower()

    if platform == 'all':
        stream_events = []

        for bot in bots.values():
            stream_events.extend(bot.stream_events)
    else:
        bot = bots.get(platform)

        if bot is None:
            return 'Unknown platform', 404

        stream_events = bot.stream_events

    messages = []

    for event in stream_events:
        if event.get('event') != 'message':
            continue

        username = escape(str(event.get('username', 'Unknown')))
        message = escape(str(event.get('message', '')))
        event_platform = escape(str(event.get('platform', platform)))

        messages.append(f'''
            <div class='message'>
                <span class='platform'>[{event_platform}]</span>
                <span class='username'>{username}</span>
                <span class='text'>{message}</span>
            </div>
        ''')

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{platform.title()} Chat</title>

        <style>
            body {{
                margin: 0;
                background: #111;
                color: white;
                font-family: Arial, sans-serif;
            }}

            #chat {{
                padding: 20px;
            }}

            .message {{
                padding: 5px 0;
            }}

            .platform {{
                color: #888;
                margin-right: 6px;
            }}

            .username {{
                font-weight: bold;
                margin-right: 6px;
            }}

            .text {{
                color: #ddd;
            }}
        </style>
    </head>

    <body>
        <div id='chat'>
            {''.join(messages)}
        </div>
    </body>
    </html>
    '''

flask.run()
