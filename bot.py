#!/usr/bin/env python3.6

import json
import time
import asyncio
import textwrap
import datetime as dt
import threading
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import uwsgi
from django.conf import settings
from constance import config
import slack
import gerrit
import django
from slackbot.models import Crontab, SentMessage, ReviewRequest


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
            return ""
        elif self.ver == gerrit.Verified.VERIFIED:
            return slack.Emoji.WHITE_CHECK_MARK
        elif self.ver == gerrit.Verified.FAILED:
            return slack.Emoji.X

    @property
    def color(self):
        if self.cr == gerrit.CodeReview.PLUS_TWO:
            return "#36a64f"
        elif (
            self.cr == gerrit.CodeReview.PLUS_ONE
            and self.ver == gerrit.Verified.VERIFIED
        ):
            return "#DBF32D"
        else:
            return "#EC1313"

    def full_message(self):
        text = f"CR: {self.code_review_icon} V: {self.verified_icon} {self.username}: {self.subject}"
        # we count every icon as one character long
        icon_lenghts = len(self.code_review_icon) + len(self.verified_icon)
        # Slack wraps lines around this width, so if we cut out here explicitly,
        # every patch will fit in one line.
        return textwrap.shorten(text, width=76 + icon_lenghts - 2, placeholder="…")


class CronJob:
    def __init__(self, gerrit_url, bot_access_token, crontab, loop, session):
        self._loop = loop
        self._gerrit = gerrit.AsyncApi(gerrit_url, session)
        self._slack = slack.AsyncApi(bot_access_token, session)

        self._crontab = crontab
        self._channel_id = crontab.channel_id
        self._crontab_changes_url = self._gerrit.changes_url(crontab.gerrit_query)

    def __str__(self):
        return f"{self._crontab.gerrit_query} -> {self._channel_id}"

    def __repr__(self):
        return f"CronJob(query='{self._crontab.gerrit_query}', channel='{self._channel_id}')"

    async def run(self):
        await self._delete_previous_messages()
        await self._handle_crontab()
        await self._handle_review_requests()

    async def _delete_previous_messages(self):
        for sent_message in SentMessage.objects.filter(crontab=self._crontab):
            # we need to delete one by one, because it's posting chat.delete to slack
            await self._loop.run_in_executor(None, sent_message.delete)

    async def _handle_crontab(self):
        if self._crontab.for_review_request_only:
            return
        crontab_gerrit_changes = await self._gerrit.get_changes(self._crontab.gerrit_query)
        crontab_changes = [PostableChange(c) for c in crontab_gerrit_changes]

        if not crontab_changes:
            print("No crontab changes")
            return

        json_res = await self._post_to_slack(
            f"{len(crontab_changes)} patch vár review-ra:",
            self._crontab_changes_url,
            crontab_changes,
        )
        self._save_message(json_res)

    async def _handle_review_requests(self):
        rrs_and_changes = await self._get_review_request_changes()
        remaining_changes = self._delete_plus_two_rrs(rrs_and_changes)
        review_request_changes = [PostableChange(c) for c in remaining_changes]

        if not review_request_changes:
            print("No new review request changes")
            return

        json_res = await self._post_to_slack(
            f"{len(review_request_changes)} külső patch vár review-ra:",
            config.GERRIT_URL,
            review_request_changes,
        )
        self._save_message(json_res)

    async def _get_review_request_changes(self):
        rrs_and_changes = []
        for rr in ReviewRequest.objects.filter(channel_id=self._channel_id):
            # TODO: These can be awaited and returned at once at the end,
            # don't need to wait for every request one by one
            gerrit_changes = await self._gerrit.get_changes(rr.gerrit_query)
            rrs_and_changes.append((rr, gerrit_changes))
        return rrs_and_changes

    def _delete_plus_two_rrs(self, rrs_and_changes):
        plus_two_rr_pks = []
        remaining_changes = []

        for rr, gerrit_changes in rrs_and_changes:
            if all(c.code_review == gerrit.CodeReview.PLUS_TWO for c in gerrit_changes):
                plus_two_rr_pks.append(rr.pk)
            else:
                remaining_changes.extend(gerrit_changes)

        ReviewRequest.objects.filter(pk__in=plus_two_rr_pks).delete()

        return remaining_changes

    async def _post_to_slack(self, summary_text, changes_url, changes):
        summary_link = slack.make_link(changes_url, summary_text)
        attachments = [
            slack.make_attachment(c.color, c.full_message(), c.url) for c in changes
        ]
        return await self._slack.post_message(
            self._channel_id, summary_link, attachments
        )

    def _save_message(self, json_res):
        sm = SentMessage(
            crontab=self._crontab,
            ts=json_res["message"]["ts"],
            channel_id=json_res["channel"],
            message=json.dumps(json_res["message"]),
        )
        sm.save()
        return sm


class MuleMessage:
    RELOAD = b"reload"


should_reload = threading.Event()


def pause():
    uwsgi.lock()


def resume():
    uwsgi.unlock()


def block_if_paused():
    was_locked = uwsgi.is_locked()
    if was_locked:
        print("Bot is paused, waiting for resume...")
    uwsgi.lock()
    uwsgi.unlock()
    if was_locked:
        print("Resuming...")


class WaitForMessages(threading.Thread):
    daemon = True

    def run(self):
        while True:
            print("Waiting for messages...")
            message = uwsgi.mule_get_msg()
            print(f"Got {message!s} message.")
            if message == MuleMessage.RELOAD:
                should_reload.set()


def make_cronjobs(loop, session):
    print("Loading settings and crontabs from db...")
    gerrit_url = config.GERRIT_URL
    bot_access_token = config.BOT_ACCESS_TOKEN

    cronjobs = []
    for crontab in Crontab.objects.all():
        cronjob = CronJob(gerrit_url, bot_access_token, crontab, loop, session)
        cronjobs.append((crontab, cronjob))

    print("Cronjobs:", cronjobs)
    return cronjobs


def get_rounded_now():
    now = dt.datetime.now(dt.timezone.utc)
    print(now, "Checking crontabs to run...")
    return now.replace(second=0, microsecond=0)


async def run_crontabs(loop, session):
    should_reload.set()

    while True:
        block_if_paused()

        if should_reload.is_set():
            print("Reloading...")
            cronjobs = make_cronjobs(loop, session)
            should_reload.clear()

        now = get_rounded_now()

        for crontab, cronjob in cronjobs:
            if crontab.next == now:
                print("Running job...", cronjob)
                loop.create_task(cronjob.run())
                crontab.calc_next()

        await asyncio.sleep(3)


def wait_for_setup():
    while config.BOT_ACCESS_TOKEN == settings.BOT_ACCESS_TOKEN_DEFAULT:
        time.sleep(5)


def main():
    print("Started main")

    django.setup()

    if config.BOT_ACCESS_TOKEN == settings.BOT_ACCESS_TOKEN_DEFAULT:
        print(
            """
You have to configure the bot first by visiting the admin interface
Constance Config page, probably on something like:
https://<this-machine-ip>/admin/constance/config/
"""
        )
    wait_for_setup()

    print(Crontab.objects.all())
    WaitForMessages().start()

    loop = asyncio.get_event_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=1))
    session = aiohttp.ClientSession(loop=loop)
    try:
        loop.run_until_complete(run_crontabs(loop, session))
    finally:
        loop.run_until_complete(session.close())


if __name__ == "__main__":
    main()
