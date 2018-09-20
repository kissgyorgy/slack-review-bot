from django.core.cache import cache
from constance import config
import slack


def cache_channels():
    slack_api = slack.Api(config.BOT_ACCESS_TOKEN)
    all_channels = slack_api.list_all_channels()
    cache.set_many({c["name"]: c for c in all_channels})


def get_channel_id(channel_name):
    channel_name = channel_name.lstrip("#")
    if cache.get(channel_name) is None:
        cache_channels()
    channel = cache.get(channel_name)
    print("Got channel from cache", channel)
    return channel["id"] if channel is not None else None
