import datetime as dt
from django.db import models
from croniter import croniter
from constance import config
import slack


class Crontab(models.Model):
    channel_name = models.CharField(max_length=100, blank=True)
    channel_id = models.CharField(
        max_length=30,
        blank=True,
        help_text="Slack internal channel ID, will be "
        "automatically set based on channel_name",
    )
    gerrit_query = models.CharField(max_length=255)
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
            self._cron = croniter(self.crontab, start_time=dt.datetime.now())
            self.calc_next()

    def __str__(self):
        return f"{self.crontab}: {self.gerrit_query} -> {self.channel_name}"

    def calc_next(self):
        self.next = self._cron.get_next(dt.datetime)


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

    def _delete_slack_channel(self):
        print(f"Deleting message {self.ts} from channel {self.channel_id}")
        slack_channel = slack.Channel(config.BOT_ACCESS_TOKEN, self.channel_id)
        return slack_channel.delete_message(self.ts)

    def delete(self, *args, **kwargs):
        res_json = self._delete_slack_channel()
        if res_json is not None:
            return super().delete(*args, **kwargs)
        return 0, {"slackbot.SentMessage": 0}

    def force_delete(self, *args, **kwargs):
        self._delete_slack_channel()
        return super().delete(*args, **kwargs)


class MuleMessage:
    RELOAD = b"reload"
    RESTART = b"restart"
    SEND_NOW = b"send_now"
