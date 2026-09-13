import bots
def start_bots(**kwargs):
    twitch = bots.TwithBot(
        twitch_refresh_token=kwargs.get('twitch_refresh_token'),
        twitch_token_id=kwargs.get('twitch_token_id'),
        twitch_token_secret=kwargs.get('twitch_token_secret'),
        twitch_broadcaster=kwargs.get('twitch_broadcaster'),
        twitch_bot=kwargs.get('twitch_bot'),
        flask=kwargs.get('flask')
    )
    youtube = bots.YoutubeBot(
        youtube_channel=kwargs.get('youtube_channel'),
        flask=kwargs.get('flask')
    )
    obs = bots.OBS(
        obs_host=kwargs.get('obs_host'),
        obs_port=kwargs.get('obs_port'),
        obs_password=kwargs.get('obs_password'),
        flask=kwargs.get('flask')
    )
    gpt = bots.GPT(
        gpt_api_key=kwargs.get('gpt_api_key'),
        flask=kwargs.get('flask')
    )
    spotify = bots.Spotify(
        spotify_client_id=kwargs.get('spotify_client_id'),
        spotify_client_secret=kwargs.get('spotify_client_secret'),
        flask=kwargs.get('flask')
    )
    return {
        'twitch': twitch,
        'youtube': youtube,
        'obs': obs,
        'gpt': gpt,
        'spotify': spotify
    }