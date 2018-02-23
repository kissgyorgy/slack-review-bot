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


class _ApiBase:
    def __init__(self, token):
        self._token = token

    def _get(self, method, payload=None):
        headers = {'Authorization': 'Bearer ' + self._token}
        return requests.get(f'{SLACK_API_URL}/{method}', payload, headers=headers)

    def _post(self, method, payload=None):
        print('Sending things', payload)
        headers = {
            'Authorization': 'Bearer ' + self._token,
            # Slack needs a charset, otherwise it will send a warning in every response...
            'Content-Type': 'application/json; charset=utf-8',
        }
        return requests.post(f'{SLACK_API_URL}/{method}', headers=headers, json=payload)


class Api(_ApiBase):
    def list_channels(self):
        return self._get('channels.list').json()

    def list_groups(self):
        return self._get('groups.list').json()

    def get_channel_id(self, channel_name):
        name = channel_name.lstrip('#')
        return self._public_channel(name) or self._private_channel(name) or None

    def _public_channel(self, name):
        for channel in self.list_channels()['channels']:
            if channel['name'] == name:
                return channel['id']

    def _private_channel(self, name):
        for group in self.list_groups()['groups']:
            if group['name'] == name:
                return group['id']


class Channel(_ApiBase):
    def __init__(self, bot_token, channel_id):
        super().__init__(bot_token)
        self._channel_id = channel_id

    def __str__(self):
        return self._channel_id

    def _get(self, method):
        return super()._get(method, {'channel': self._channel_id})

    def _post(self, method, payload):
        payload.update({'channel': self._channel_id})
        return super()._post(method, payload)

    def info(self):
        return self._get('channels.info')

    def delete_message(self, ts):
        return self._post('chat.delete', {'ts': ts})

    def post_message(self, text, attachments):
        return self._post('chat.postMessage', {'text': text, 'attachments': attachments})


class App:
    SCOPE = 'commands,bot'

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
