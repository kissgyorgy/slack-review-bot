import datetime as dt
from django.db import models
from django.utils import timezone
from croniter import croniter
from constance import config
import slack
import gerrit


class Crontab(models.Model):
    channel_name = models.CharField(max_length=100, blank=True)
    channel_id = models.CharField(
        max_length=30,
        blank=True,
        help_text="Slack internal channel ID, will be "
        "automatically set based on channel_name",
    )
    gerrit_query = models.CharField(max_length=255, blank=True)
    crontab = models.CharField(
        max_length=255,
        help_text='Examples: <a href="https://crontab.guru/" target="_blank">crontab.guru<a>',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is a new, empty object, there is no crontab value set yet
        if self.pk is None:
            self._cron = None
            self.next = None
        else:
            # This way, we will miss this very minute at startup to avoid sending the same message twice
            self._cron = croniter(self.crontab, start_time=timezone.localtime())
            self.calc_next()

    def __str__(self):
        return f"{self.crontab}: {self.gerrit_query} -> {self.channel_name}"

    def calc_next(self):
        next_dt = self._cron.get_next(dt.datetime)
        self.next = next_dt.astimezone(dt.timezone.utc)

    @property
    def for_review_request_only(self):
        # empty gerrit_query field means, it is used only for ReviewRequests
        return not self.gerrit_query


class SentMessage(models.Model):
    crontab = models.ForeignKey(
        Crontab,
        on_delete=models.SET_NULL,
        related_name="sent_messages",
        blank=True,
        null=True,
    )

    ts = models.CharField(max_length=30)
    channel_id = models.CharField(max_length=30)
    message = models.TextField(
        help_text='JSON serialized slack response "message" field to a chat.PostMessage'
    )

    def __str__(self):
        return self.ts

    def _delete_slack_message(self):
        print(f"Deleting message {self.ts} from channel {self.channel_id}")
        slack_api = slack.Api(config.BOT_ACCESS_TOKEN)
        slack_api.delete_message(self.channel_id, self.ts)

    def delete(self, *args, **kwargs):
        try:
            self._delete_slack_message()
        except slack.ApiError:
            return 0, {"slackbot.SentMessage": 0}
        else:
            return super().delete(*args, **kwargs)

    def force_delete(self, *args, **kwargs):
        try:
            self._delete_slack_message()
        finally:
            return super().delete(*args, **kwargs)


class ReviewRequest(models.Model):
    crontab = models.ForeignKey(
        Crontab,
        on_delete=models.SET_NULL,
        related_name="review_requests",
        blank=True,
        null=True,
    )
    ts = models.CharField(max_length=30, help_text="The message ts of the requests")
    slack_user_id = models.CharField(
        max_length=30, help_text="The Slack user who sent the request"
    )
    channel_id = models.CharField(
        max_length=30, help_text="The channel where this requests is sent to originally"
    )
    gerrit_url = models.URLField()
    gerrit_query = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.gerrit_url


class MuleMessage:
    RELOAD = b"reload"
    RESTART = b"restart"
    SEND_NOW = b"send_now"
