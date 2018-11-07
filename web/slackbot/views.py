import asyncio
from django.views import generic
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.http import require_POST
from constance import config
import aiohttp
import slack
from . import models as m
from . import forms as f

try:
    import bot
except ImportError:
    # manage.py commands need to run without uwsgi
    pass


class HomeView(generic.ListView):
    model = m.Crontab
    context_object_name = "crontabs"
    template_name = "home.html"


class UsageView(generic.TemplateView):
    template_name = "usage.html"


class CrontabCreateView(generic.CreateView):
    model = m.Crontab
    form_class = f.CrontabCreateForm
    template_name = "new_crontab.html"
    success_url = "/"

    def form_valid(self, form):
        messages.success(self.request, "Crontab has been created")
        return super().form_valid(form)


class CrontabEditView(generic.UpdateView):
    model = m.Crontab
    template_name = "edit_crontab.html"
    form_class = f.CrontabEditForm
    success_url = "/"


class CrontabDeleteView(generic.DeleteView):
    model = m.Crontab
    success_url = "/"

    def get_success_url(self):
        messages.info(self.request, f'Crontab "{self.object}" has been deleted')
        return super().get_success_url()


@require_POST
def pause_bot(request):
    bot.pause()
    return redirect("/")


@require_POST
def resume_bot(request):
    bot.resume()
    messages.info(request, "Bot resumed")
    return redirect("/")


@transaction.atomic
def slack_oauth(request):
    get_state = request.GET.get("state")
    session_state = request.session.get("oauth_state")
    if get_state is None or session_state is None or get_state != session_state:
        raise SuspiciousOperation(
            "Invalid state. You have been logged and will be caught."
        )

    error = request.GET.get("error")
    if error == "access_denied":
        messages.error(request, "Access denied - Request cancelled")
        return redirect("/")
    elif error is not None:
        messages.error(request, "Unknown error - try again")
        return redirect("/")

    slack_app = slack.App(
        config.SLACK_CLIENT_ID, config.SLACK_CLIENT_SECRET, config.SLACK_REDIRECT_URI
    )
    res = slack_app.request_oauth_token(request.GET["code"])
    print(res)

    if not res["ok"]:
        messages.error(
            request, "Permission has been granted, but OAuth token request has failed"
        )
        return redirect("/")

    # These are database operations through the constance app
    config.ACCESS_TOKEN = res["access_token"]
    config.SCOPE = res["scope"]
    config.USER_ID = res["user_id"]
    config.TEAM_NAME = res["team_name"]
    config.TEAM_ID = res["team_id"]
    config.BOT_USER_ID = res["bot"]["bot_user_id"]
    config.BOT_ACCESS_TOKEN = res["bot"]["bot_access_token"]

    messages.success(request, "Succesfully installed Slackbot.")
    return redirect("/")


@require_POST
def run_crontab(request, crontab_id):
    crontab = m.Crontab.objects.get(pk=crontab_id)
    loop = asyncio.get_event_loop()
    session = aiohttp.ClientSession(loop=loop)
    cronjob = bot.CronJob(
        config.GERRIT_URL, config.BOT_ACCESS_TOKEN, crontab, loop, session
    )
    loop.run_until_complete(cronjob.run())
    loop.run_until_complete(session.close())

    messages.success(request, "Patch set updated.")
    return redirect("/")
