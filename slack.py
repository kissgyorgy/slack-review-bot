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


def make_link(url, text):
    return f'<{url}|{text}>'


def make_attachment(color, author_name, author_link):
    return {'color': color, 'author_name': author_name, 'author_link': author_link}


def revoke_token(token):
    return requests.post(SLACK_API_URL + '/auth.revoke', {'token': token})


class Channel:
    def __init__(self, webhook_url, channel):
        self._webhook_url = webhook_url
        self._channel = channel

    def __str__(self):
        return self._channel

    def post(self, text, attachments):
        payload = {'text': text, 'attachments': attachments, 'channel': self._channel}
        return requests.post(self._webhook_url, json=payload)


class App:
    SCOPE = 'incoming-webhook,bot'

    def __init__(self, client_id, client_secret, redirect_uri):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def request_oauth_token(self, code):
        # documentation: https://api.slack.com/methods/oauth.access
        res = requests.post(SLACK_API_URL + '/oauth.access', {
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'redirect_uri': self._redirect_uri,
            'code': code,
        })
        # example in slack_messages/oauth.access.json
        return res.json()

    def make_button_url(self, state):
        params = urlencode({
            'scope': self.SCOPE,
            'client_id': self._client_id,
            'redirect_uri': self._redirect_uri,
            'state': state,
        })
        return f'{SLACK_OAUTH_URL}?{params}'
