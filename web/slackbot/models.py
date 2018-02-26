import datetime as dt
from croniter import croniter
from constance import config
from django.db import models
import slack


class Crontab(models.Model):
    channel_name = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=30, blank=True)
    gerrit_query = models.CharField(max_length=255)
    crontab = models.CharField(max_length=255)

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
        return f'{self.crontab}: {self.gerrit_query} -> {self.channel_name}'

    def save(self, *args, **kwargs):
        slack_api = slack.Api(config.BOT_ACCESS_TOKEN)
        # TODO: cache the channels.info result for faster lookup
        self.channel_id = slack_api.get_channel_id(self.channel_name)
        return super().save(*args, **kwargs)

    def calc_next(self):
        self.next = self._cron.get_next(dt.datetime)


class SentMessage(models.Model):
    crontab = models.ForeignKey(Crontab, on_delete=models.SET_NULL, related_name='sent_messages',
                                blank=True, null=True)

    ts = models.CharField(max_length=30)
    channel_id = models.CharField(max_length=30)
    message = models.TextField(help_text='JSON serialized slack response "message" field to a chat.PostMessage')

    def __str__(self):
        return self.ts

    def delete(self, *args, **kwargs):
        slack_channel = slack.Channel(config.BOT_ACCESS_TOKEN, self.channel_id)
        res = slack_channel.delete_message(self.ts)
        if res.ok and res.json()['ok']:
            print(f'Deleting message {self.ts} from channel {self.channel_id}')
            return super().delete(*args, **kwargs)
        else:
            print(f'{res.status_code} error deleting {self.ts} for channel {self._slack_channel}: {res.text}')


class MuleMessage:
    RELOAD = b'reload'
    RESTART = b'restart'
    SEND_NOW = b'send_now'
