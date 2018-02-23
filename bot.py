#!/usr/bin/env python3.6

import sys
import time
import textwrap
import datetime as dt
from croniter import croniter
import slack
import gerrit
import database


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


class CronTime:
    def __init__(self, crontab):
        self._crontab = crontab
        # This way, we will miss this very minute at startup to avoid sending the same message twice.
        self._cron = croniter(crontab, start_time=dt.datetime.now())
        self.calc_next()

    def __str__(self):
        return self._crontab

    def __repr__(self):
        return f'CronTime({self._crontab})'

    def calc_next(self):
        self.next = self._cron.get_next(dt.datetime)


class CronJob:
    def __init__(self, gerrit_url, gerrit_query, bot_token, slack_channel_id, db):
        self._gerrit = gerrit.Client(gerrit_url, gerrit_query)
        self._slack_channel = slack.Channel(bot_token, slack_channel_id)
        self._slack_channel_id = slack_channel_id
        self._db = db

    def __str__(self):
        return f'{self._gerrit.query} -> {self._slack_channel}'

    def __repr__(self):
        return f"CronJob(query='{self._gerrit.query}', channel='{self._slack_channel}')"

    def run(self):
        changes = [PostableChange(c) for c in self._gerrit.get_changes()]
        if not changes:
            self._delete_sent_messages()
            print('No changes')
            return True

        res = self._post_to_slack(changes)
        if res.ok:
            self._delete_sent_messages()
            print('GOT RESPONSE', res.text)
            json_res = res.json()
            message = database.SentMessage(json_res['message']['ts'], json_res['channel'], json_res['message']['text'])
            self._db.save_sent_message(message)
        else:
            print(f'{res.status_code} error requesting {res.url} for channel {self._slack_channel}:',
                  res.text, file=sys.stderr)
            return False

        return True

    def _post_to_slack(self, changes):
        summary_text = f'{len(changes)} patch vár review-ra:'
        summary_link = slack.make_link(self._gerrit.changes_url, summary_text)
        attachments = [slack.make_attachment(c.color, c.full_message(), c.url) for c in changes]
        return self._slack_channel.post_message(summary_link, attachments)

    def _delete_sent_messages(self):
        for m in self._db.load_sent_messages(self._slack_channel_id):
            res = self._slack_channel.delete_message(m.ts)
            if res.ok and res.json()['ok']:
                self._db.delete_sent_message(m)


def main():
def load_db():
    print('Loading settings and crontabs from db...')
    db = database.Database()
    environment = db.load_environment()
    gerrit_url = environment.GERRIT_URL
    bot_access_token = environment.BOT_ACCESS_TOKEN
    return db, gerrit_url, bot_access_token


def make_crontab(db, gerrit_url, bot_access_token):
    print('Crontabs:')
    crontab = []
    for c in db.load_all_crontabs():
        crontime = CronTime(c.crontab)
        cronjob = CronJob(gerrit_url, c.gerrit_query, bot_access_token, c.channel_id, db)
        crontab.append((crontime, cronjob))

    print(crontab)
    return crontab


def main():
    print('Started main')
    should_reload.set()

    while True:
            db, gerrit_url, bot_access_token = load_db()
            crontab = make_crontab(db, gerrit_url, bot_access_token)

        now = dt.datetime.now()
        rounded_now = now.replace(second=0, microsecond=0)
        print(now, 'Checking crontabs to run...')

        for crontime, cronjob in crontab:
            if crontime.next == rounded_now:
                print('Running job...', cronjob)
                cronjob.run()
                crontime.calc_next()

        time.sleep(5)


if __name__ == '__main__':
    main()
