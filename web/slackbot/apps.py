from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
try:
    import uwsgi
    from bot import MuleMessage
    is_uwsgi_running = True
except ImportError:
    is_uwsgi_running = False


def reload_mule(sender, **kwargs):
    uwsgi.mule_msg(MuleMessage.RELOAD)


class SlackbotConfig(AppConfig):
    name = 'slackbot'

    def ready(self):
        if is_uwsgi_running:
            post_save.connect(reload_mule, sender='slackbot.Crontab')
            post_delete.connect(reload_mule, sender='slackbot.Crontab')
