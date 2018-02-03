#!/usr/bin/env python3.6

import sys
import textwrap
import slack
import gerrit


class PostableChange:
    def __init__(self, gerrit_change):
        self._gerrit_change = gerrit_change

    @property
    def cr(self):
        return self._gerrit_change.code_review

    @property
    def ver(self):
        return self._gerrit_change.verified

    @property
    def username(self):
        return self._gerrit_change.username

    @property
    def subject(self):
        return slack.escape(self._gerrit_change.subject)

    @property
    def code_review_icon(self):
        if self.cr == gerrit.CodeReview.PLUS_ONE:
            return slack.Emoji.PLUS_ONE
        elif self.cr == gerrit.CodeReview.PLUS_TWO:
            return slack.Emoji.PLUS_ONE * 2
        elif self.cr == gerrit.CodeReview.MISSING:
            return slack.Emoji.EXCLAMATION
        elif self.cr == gerrit.CodeReview.MINUS_ONE:
            return slack.Emoji.POOP
        elif self.cr == gerrit.CodeReview.MINUS_TWO:
            return slack.Emoji.JS

    @property
    def verified_icon(self):
        if self.ver == gerrit.Verified.MISSING:
            return ''
        elif self.ver == gerrit.Verified.VERIFIED:
            return slack.Emoji.WHITE_CHECK_MARK
        elif self.ver == gerrit.Verified.FAILED:
            return slack.Emoji.X

    @property
    def color(self):
        if self.cr == gerrit.CodeReview.PLUS_TWO:
            return '#36a64f'
        elif self.cr == gerrit.CodeReview.PLUS_ONE and self.ver == gerrit.Verified.VERIFIED:
            return '#DBF32D'
        else:
            return '#EC1313'


def run(gerrit_url, gerrit_query, slack_webhook_url, slack_channel=None):
    gerrit_changes = gerrit.get_changes(gerrit_url, gerrit_query)
    changes = [PostableChange(c) for c in gerrit_changes]
    if not changes:
        return True

    slack_client = slack.SlackClient(slack_webhook_url, slack_channel)
    summary_link = _make_summary(gerrit_url, gerrit_query, changes)
    attachments = [slack.make_attachment(c.color, _make_message(c), c.url) for c in changes]

    res = slack_client.post(summary_link, attachments)
    if not res.ok:
        print(res.status_code, 'error:', res.text, file=sys.stderr)
        return False

    return True


def _make_summary(gerrit_url, gerrit_query, gerrit_changes):
    gerrit_changes_url = gerrit.make_changes_url(gerrit_url, gerrit_query)
    link_text = f'{len(gerrit_changes)} patch vár review-ra:'
    return slack.make_link(gerrit_changes_url, link_text)


def _make_message(change):
    text = f'CR: {change.code_review_icon} V: {change.verified_icon} - {change.username}: {change.subject}'
    # Slack wraps lines around 80? width, so if we cut out here explicitly,
    # every patch will fit in one line
    return textwrap.shorten(text, width=80, placeholder=' …')
