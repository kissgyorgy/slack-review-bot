import os
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


def post(changes):
    payload = {
        'channel': os.environ['CHANNEL'],
        'text': '{} patch vár review-ra:'.format(len(changes)),
        'attachments': _make_attachments(changes),
    }
    print('Payload:', payload, flush=True)
    requests.post(os.environ['SLACK_WEBHOOK_URL'], json=payload)


def _make_attachments(changes):
    attachments = []
    for change in changes:
        attach = {
            'color': change.color,
            'author_name': '{c.author}: {c.subject}'.format(c=change),
            'author_link': change.url,
            'mrkdwn_in': ['fields'],
            'fields': [
                {
                    'value': 'Code-Review: {.code_review}'.format(change),
                    'short': True,
                },
                {
                    'value': 'Verified: {.verified}'.format(change),
                    'short': True,
                }
            ]
        }
        attachments.append(attach)

    return attachments
