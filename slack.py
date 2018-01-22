import requests


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
    escaped = text.replace('<', '&lt;')
    escaped = escaped.replace('>', '&gt;')
    escaped = escaped.replace('&', '&amp;')
    return escaped


class SlackClient:
    def __init__(self, webhook_url, channel):
        self._webhook_url = webhook_url
        self._channel = channel

    def post(self, text, attachments):
        payload = {'channel': self._channel, 'text': text, 'attachments': attachments}
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
        'code': code,
    })
    # example in slack_messages/oauth.access.json
    return res.json()


def revoke_token(token):
    return requests.post(SLACK_API_URL + '/auth.revoke', {'token': token})


def make_button_url(env, state):
    return f'{SLACK_OAUTH_URL}?scope=incoming-webhook&client_id={env.SLACK_CLIENT_ID}&state={state}'
