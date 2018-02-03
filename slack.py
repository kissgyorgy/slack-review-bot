from urllib.parse import urlencode
import requests


class Emoji:
    PLUS_ONE = ':+1:'
    POOP = ':poop:'
    JS = ':js:'
    EXCLAMATION = ':exclamation:'
    WHITE_CHECK_MARK = ':white_check_mark:'
    X = ':x:'


SLACK_API_URL = 'https://slack.com/api'
SLACK_OAUTH_URL = 'https://slack.com/oauth/authorize'


def escape(text):
    """Escape Slack special characters.
    See: https://api.slack.com/docs/message-formatting#how_to_escape_characters
    """
    rv = text.replace('<', '&lt;')
    rv = rv.replace('>', '&gt;')
    rv = rv.replace('&', '&amp;')
    return rv


class SlackClient:
    def __init__(self, webhook_url, channel=None):
        self._webhook_url = webhook_url
        self._channel = channel

    def post(self, text, attachments):
        payload = {'text': text, 'attachments': attachments}
        # Channel doesn't matter if used as a proper Slack app, because webhook_url is tied to a channel anyway.
        # It only matters if there is one global incoming webhook configured.
        if self._channel is not None:
            payload['channel'] = self._channel
        return requests.post(self._webhook_url, json=payload)


def make_link(url, text):
    return f'<{url}|{text}>'


def make_attachment(color, author_name, author_link):
    return {'color': color, 'author_name': author_name, 'author_link': author_link}


def request_oauth_token(env, code):
    # documentation: https://api.slack.com/methods/oauth.access
    res = requests.post(SLACK_API_URL + '/oauth.access', {
        'client_id': env.SLACK_CLIENT_ID,
        'client_secret': env.SLACK_CLIENT_SECRET,
        'redirect_uri': env.SLACK_REDIRECT_URI,
        'code': code,
    })
    # example in slack_messages/oauth.access.json
    return res.json()


def revoke_token(token):
    return requests.post(SLACK_API_URL + '/auth.revoke', {'token': token})


def make_button_url(env, state):
    params = urlencode({
        'scope': 'incoming-webhook',
        'client_id': env.SLACK_CLIENT_ID,
        'state': state,
        'redirect_uri': env.SLACK_REDIRECT_URI,
    })
    return f'{SLACK_OAUTH_URL}?{params}'
