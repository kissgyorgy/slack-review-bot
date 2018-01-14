import requests


PLUS_ONE = ':+1:'
POOP = ':poop:'
JS = ':js:'
EXCLAMATION = ':exclamation:'

WHITE_CHECK_MARK = ':white_check_mark:'
X = ':x:'


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
    return '<{}|{}>'.format(url, text)


def make_attachment(color, author_name, author_link):
    return {'color': color, 'author_name': author_name, 'author_link': author_link}
