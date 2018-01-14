#!/usr/bin/env python3

import os
import sys
import textwrap
import slack
import gerrit


class ChangeConfig:
    GERRIT_URL = 'https://review.balabit'
    QUERY = os.environ['QUERY']

    ESCAPER = slack.escape
    LINK_MAKER = slack.make_link

    PLUS_ONE = slack.PLUS_ONE
    PLUS_TWO = slack.PLUS_ONE * 2
    MINUS_ONE = slack.POOP
    MINUS_TWO = slack.JS
    MISSING = slack.EXCLAMATION

    VERIFIED = slack.WHITE_CHECK_MARK
    FAILED = slack.X

    GREEN = '#36a64f'
    YELLOW = '#DBF32D'
    RED = '#EC1313'


class SlackConfig:
    WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
    CHANNEL = os.environ['CHANNEL']


def main(change_config, slack_config):
    gerrit_changes = gerrit.get_changes(change_config)
    if not gerrit_changes:
        return 0

    slack_client = slack.SlackClient(slack_config.WEBHOOK_URL, slack_config.CHANNEL)
    summary_link = _make_summary(change_config, gerrit_changes)
    attachments = [slack.make_attachment(c.color, _make_message(c), c.url) for c in gerrit_changes]

    res = slack_client.post(summary_link, attachments)
    if not res.ok:
        print(res.status_code, 'error:', res.text, file=sys.stderr)
        return 1

    return 0


def _make_summary(change_config, gerrit_changes):
    gerrit_changes_url = gerrit.make_changes_url(change_config)
    link_text = '{} patch vár review-ra:'.format(len(gerrit_changes))
    return slack.make_link(gerrit_changes_url, link_text)


def _make_message(gerrit_change):
    text = 'CR: {c.code_review} V: {c.verified} - {c.author}: {c.subject}'.format(c=gerrit_change)
    # Slack wraps lines around 80? width, so if we cut out here explicitly,
    # every patch will fit in one line
    return textwrap.shorten(text, width=80, placeholder=' …')


if __name__ == '__main__':
    exit_code = main(ChangeConfig, SlackConfig)
    sys.exit(exit_code)
