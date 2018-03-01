#!/usr/bin/env python3.6

import time
import textwrap
import datetime as dt
import threading
import uwsgi
from constance import config
import slack
import gerrit
import django
from slackbot.models import Crontab, SentMessage


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
    def url(self):
        return self._gerrit_change.url

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

    def full_message(self):
        text = f'CR: {self.code_review_icon} V: {self.verified_icon} {self.username}: {self.subject}'
        # we count every icon as one character long
        icon_lenghts = len(self.code_review_icon) + len(self.verified_icon)
        # Slack wraps lines around this width, so if we cut out here explicitly,
        # every patch will fit in one line.
        return textwrap.shorten(text, width=76+icon_lenghts-2, placeholder='…')


class CronJob:
    def __init__(self, gerrit_url, bot_access_token, crontab):
        self._gerrit = gerrit.Client(gerrit_url, crontab.gerrit_query)
        self._slack_channel = slack.Channel(bot_access_token, crontab.channel_id)
        self._crontab = crontab

    def __str__(self):
        return f'{self._gerrit.query} -> {self._slack_channel}'

    def __repr__(self):
        return f"CronJob(query='{self._gerrit.query}', channel='{self._slack_channel}')"

    def run(self):
        changes = [PostableChange(c) for c in self._gerrit.get_changes()]
        if not changes:
            self._delete_previous_messages()
            print('No changes')
            return

        json_res = self._post_to_slack(changes)
        if json_res is None:
            return

        just_sent = self._save_message(json_res)
        self._delete_previous_messages(just_sent)

    def _post_to_slack(self, changes):
        summary_text = f'{len(changes)} patch vár review-ra:'
        summary_link = slack.make_link(self._gerrit.changes_url, summary_text)
        attachments = [slack.make_attachment(c.color, c.full_message(), c.url) for c in changes]
        return self._slack_channel.post_message(summary_link, attachments)

    def _delete_previous_messages(self, just_sent):
        for sm in SentMessage.objects.filter(crontab=self._crontab)\
                                     .exclude(pk=just_sent.pk):
            # we need to delete one by one, because it's posting chat.delete to slack
            sm.delete()

    def _save_message(self, json_res):
        jsm = json_res['message']
        sm = SentMessage(crontab=self._crontab, ts=jsm['ts'], channel_id=json_res['channel'], message=jsm)
        sm.save()
        return sm


class MuleMessage:
    RELOAD = b'reload'
    RESTART = b'restart'
    SEND_NOW = b'send_now'


should_reload = threading.Event()


class WaitForMessages(threading.Thread):
    daemon = True

    def run(self):
        while True:
            print('Waiting for messages...')
            message = uwsgi.mule_get_msg()
            if message == MuleMessage.RELOAD:
                print('Got reload message.')
                should_reload.set()


def make_cronjobs():
    print('Loading settings and crontabs from db...')
    gerrit_url = config.GERRIT_URL
    bot_access_token = config.BOT_ACCESS_TOKEN

    cronjobs = []
    for crontab in Crontab.objects.all():
        cronjob = CronJob(gerrit_url, bot_access_token, crontab)
        cronjobs.append((crontab, cronjob))

    print('Cronjobs:', cronjobs)
    return cronjobs


def main():
    print('Started main')
    should_reload.set()

    while True:
        if should_reload.is_set():
            print('Reloading...')
            cronjobs = make_cronjobs()
            should_reload.clear()

        now = dt.datetime.now()
        rounded_now = now.replace(second=0, microsecond=0)
        print(now, 'Checking crontabs to run...')

        for crontab, cronjob in cronjobs:
            if crontab.next == rounded_now:
                print('Running job...', cronjob)
                cronjob.run()
                crontab.calc_next()

        time.sleep(50)


if __name__ == '__main__':
    django.setup()
    print(Crontab.objects.all())
    WaitForMessages().start()
    main()
