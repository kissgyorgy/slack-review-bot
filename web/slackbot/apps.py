from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


def reload_mule(sender, **kwargs):
    import uwsgi
    from bot import MuleMessage
    uwsgi.mule_msg(MuleMessage.RELOAD)


class SlackbotConfig(AppConfig):
    name = 'slackbot'

    def ready(self):
        post_save.connect(reload_mule, sender='slackbot.Crontab')
        post_delete.connect(reload_mule, sender='slackbot.Crontab')
