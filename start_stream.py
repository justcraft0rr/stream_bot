from start_bots import start_bots
import flask as flask_imported
from os import getenv
from html import escape
import tomllib
import logging
config = tomllib.load(open('/home/justcraft/config.toml', 'rb'))
flask = flask_imported.Flask(__name__)
stream_events = []
bots = start_bots(
    twitch_refresh_token=getenv('twitch_refresh_token'),
    twitch_token_id=getenv('twitch_client_id'),
    twitch_token_secret=getenv('twitch_client_secret'),
    twitch_broadcaster=getenv('twitch_broadcaster'),
    twitch_bot=getenv('twitch_bot'),
    kick_client_id=getenv('kick_client_id'),
    kick_client_secret=getenv('kick_client_secret'),
    kick_broadcaster=getenv('kick_broadcaster'),
    kick_webhook_url=getenv('kick_webhook_url'),
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
@flask.route("/api/chat/<platform>")
def chat_api(platform):
    platform = platform.lower()

    if platform == "all":
        stream_events = []
        seen = set()

        for bot in bots.values():
            if not hasattr(bot, "stream_events"):
                continue

            for event in bot.stream_events:
                if event.get("event") != "message":
                    continue

                event_id = (
                    event.get("platform"),
                    event.get("username"),
                    event.get("message")
                )

                if event_id in seen:
                    continue

                seen.add(event_id)
                stream_events.append(event)
    else:
        bot = bots.get(platform)

        if bot is None:
            return "Unknown platform", 404

        stream_events = bot.stream_events

    messages = []

    for event in stream_events:
        if event.get("event") != "message":
            continue

        messages.append({
            "platform": event.get("platform", platform),
            "username": event.get("username", "Unknown"),
            "message": event.get("message", "")
        })

    return flask_imported.jsonify(messages)
@flask.route("/chat/<platform>")
def chat(platform):
    platform = platform.lower()

    if platform != "all" and platform not in bots:
        return "Unknown platform", 404

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat</title>

        <style>
            html, body {
                margin: 0;
                background: transparent;
                color: white;
                font-family: Arial, sans-serif;
            }

            #chat {
                padding: 10px;
                padding-bottom: 0;
                height: calc(100vh - 80px);
                overflow-y: auto;
            }
            #chat::-webkit-scrollbar {
                display: none;
            }

            .message {
                font-size: 70px;
                padding: 2px 0;
            }

            .platform {
                color: #888;
            }

            .username {
                font-weight: bold;
                color: orange;
            }

            .text {
                color: #ddd;
            }

            .platform-icon {
                width: 60px;
                height: 60px;
                vertical-align: middle;
                margin-right: 5px;
            }
        </style>
    </head>

    <body>
        <div id="chat"><div id="chat-bottom"></div></div>

        <script>
            const platform = """ + repr(platform) + """;
            const chat = document.getElementById("chat");
            const chatBottom = document.getElementById("chat-bottom");

            async function updateChat() {
                const response = await fetch("/api/chat/" + platform);
                const messages = await response.json();

                chat.replaceChildren();

                for (const message of messages) {
                    const row = document.createElement("div");
                    row.className = "message";

                    const platformIcon = document.createElement("img");
                    platformIcon.className = "platform-icon";

                    if (message.platform === "twitch") {
                        platformIcon.src = "/static/icons/twitch.png";
                    } else if (message.platform === "kick") {
                        platformIcon.src = "/static/icons/kick.png";
                    } else if (message.platform === "youtube") {
                        platformIcon.src = "/static/icons/youtube.png";
                    }

                    const spacing = document.createElement("span");
                    spacing.className = "spacing";
                    spacing.textContent = " ";

                    const username = document.createElement("span");
                    username.className = "username";
                    username.textContent = message.username + ": ";

                    const text = document.createElement("span");
                    text.className = "text";
                    text.textContent = message.message;

                    row.append(platformIcon, spacing, username, text);
                    chat.appendChild(row);
                }
                chat.scrollTop = chat.scrollHeight;
            }

            updateChat();
            setInterval(updateChat, 1000);
        </script>
    </body>
    </html>
    """
@flask.route('/user/chat/')
def user_chat():
    return '''
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>User Chat</title>
                <style>
                    body {
                        margin: 0;
                        min-height: 400px;
                        background-color: gray;
                    }
                    ul, li {
                        list-style: none;
                        margin: 0;
                        padding: 0;
                    }
                    .send_message {
                        position: absolute;
                        bottom: 5px;
                        left: 5px;
                        right: 5px;
                        width: calc(100% - 10px);
                    }
                    ul {
                        display: flex;
                        width: 100%;
                        gap: 10px;
                    }
                    li {
                        padding: 0;
                    }
                    .message-input {
                        flex: 1;
                    }
                    .message-input input {
                        box-sizing: border-box;
                        width: 100%;
                    }
                    #chat {
                        padding: 10px;
                    }
                    .message {
                        font-size: 32px;
                        padding: 2px 0;
                    }
                    .platform {
                        color: #888;
                    }
                    .username {
                        font-weight: bold;
                        color: orange;
                    }
                    .text {
                        color: #ddd;
                    }
                    .platform-icon {
                        width: 22px;
                        height: 22px;
                        vertical-align: middle;
                        margin-right: 5px;
                    }
                </style>
            </head>

            <body>
                <div class="send_message">
                    <ul>
                        <li>
                            <div class="platform-selector">
                                <select name="platform" id="platform">
                                    <option value="all">All Platforms</option>
                                    <option value="twitch">Twitch</option>
                                    <option value="kick">Kick</option>
                                    <!-- <option value="youtube">Youtube</option> -->
                                </select>
                            </div>
                        </li>
                        <li class="message-input">
                            <input
                                type="text"
                                id="message"
                                name="message"
                                placeholder="Message..."
                            >
                        </li>
                        <li>
                            <button type="button" id="send">Send</button>
                        </li>
                    </ul>
                </div>
                <div id="chat"></div>
                <script>
                    const platform = "all";
                    const chat = document.getElementById("chat");

                    async function updateChat() {
                        const response = await fetch("/api/chat/" + platform);
                        const messages = await response.json();

                        chat.replaceChildren();

                        for (const message of messages) {
                            const row = document.createElement("div");
                            row.className = "message";

                            const platformIcon = document.createElement("img");
                            platformIcon.className = "platform-icon";

                            if (message.platform === "twitch") {
                                platformIcon.src = "/static/icons/twitch.png";
                            } else if (message.platform === "kick") {
                                platformIcon.src = "/static/icons/kick.png";
                            } else if (message.platform === "youtube") {
                                platformIcon.src = "/static/icons/youtube.png";
                            }

                            const spacing = document.createElement("span");
                            spacing.className = "spacing";
                            spacing.textContent = " ";

                            const username = document.createElement("span");
                            username.className = "username";
                            username.textContent = message.username + ": ";

                            const text = document.createElement("span");
                            text.className = "text";
                            text.textContent = message.message;

                            row.append(platformIcon, spacing, username, text);
                            chat.appendChild(row);
                        }

                        chat.scrollTop = chat.scrollHeight;
                    }

                    updateChat();
                    setInterval(updateChat, 1000);
                </script>
                <script>
                    const sendPlatform = document.getElementById("platform");
                    const sendMessageInput = document.getElementById("message");
                    const sendButton = document.getElementById("send");

                    async function sendChatMessage() {
                        const text = sendMessageInput.value.trim();

                        console.log("Sending:", {
                            platform: sendPlatform.value,
                            message: text
                        });

                        if (!text) {
                            return;
                        }

                        try {
                            const response = await fetch("/api/chat/send_message", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    platform: sendPlatform.value,
                                    message: text
                                })
                            });

                            console.log("Status:", response.status);

                            const data = await response.json();

                            console.log("Response:", data);

                            if (data.success) {
                                sendMessageInput.value = "";
                            }

                        } catch (error) {
                            console.error("Fetch error:", error);
                        }
                    }

                    sendButton.addEventListener("click", sendChatMessage);

                    sendMessageInput.addEventListener("keydown", function(event) {
                        if (event.key === "Enter") {
                            sendChatMessage();
                        }
                    });
                </script>
            </body>
        </html>
    '''
@flask.route('/api/chat/send_message', methods=['POST'])
def send_chat_message():
    data = flask_imported.request.get_json()

    platform = data.get('platform')
    message = data.get('message')

    if not platform or not message:
        return flask_imported.jsonify({
            'success': False,
            'error': 'Missing platform or message'
        }), 400

    platform = platform.lower()

    if platform == 'all':
        for platform, bot in bots.items():
            if platform in [
                'twitch',
                #'youtube',
                'kick'
            ]:
                bot.send_message(message)

    else:
        bot = bots.get(platform)

        if not bot:
            return flask_imported.jsonify({
                'success': False,
                'error': f'{platform} bot not found'
            }), 404

        bot.send_message(message)

    return flask_imported.jsonify({
        'success': True
    })
logging.getLogger('werkzeug').disabled = True
flask.run(debug=False)
