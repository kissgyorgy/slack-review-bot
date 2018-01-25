#!/usr/bin/env python3.6

import sys
import textwrap
import slack
import gerrit


def get_gerrit_changes_and_post_to_slack(gerrit_url, gerrit_query, slack_webhook_url, slack_channel):
    gerrit_changes = gerrit.get_changes(gerrit_url, gerrit_query)
    if not gerrit_changes:
        return True

    slack_client = slack.SlackClient(slack_webhook_url, slack_channel)
    summary_link = _make_summary(gerrit_changes)
    attachments = [slack.make_attachment(c.color, _make_message(c), c.url) for c in gerrit_changes]

    res = slack_client.post(summary_link, attachments)
    if not res.ok:
        print(res.status_code, 'error:', res.text, file=sys.stderr)
        return False

    return True


def _make_summary(gerrit_changes):
    gerrit_changes_url = gerrit.make_changes_url()
    link_text = f'{len(gerrit_changes)} patch vár review-ra:'
    return slack.make_link(gerrit_changes_url, link_text)


def _make_message(gerrit_change):
    text = 'CR: {c.code_review} V: {c.verified} - {c.author}: {c.subject}'.format(c=gerrit_change)
    # Slack wraps lines around 80? width, so if we cut out here explicitly,
    # every patch will fit in one line
    return textwrap.shorten(text, width=80, placeholder=' …')
