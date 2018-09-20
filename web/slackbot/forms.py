from django import forms
from django.utils.safestring import mark_safe
from constance import config
from croniter import croniter
import slack
from .channels import get_channel_id
from . import models as m


class CrontabFieldMixin:
    def clean_crontab(self):
        crontab = self.cleaned_data["crontab"]
        if not croniter.is_valid(crontab):
            raise forms.ValidationError("Invalid crontab format")
        return crontab


class CrontabCreateForm(CrontabFieldMixin, forms.ModelForm):
    class Meta:
        model = m.Crontab
        fields = ("channel_name", "channel_id", "gerrit_query", "crontab")

    def clean(self):
        cleaned_data = super().clean()
        channel_name = cleaned_data.get("channel_name")
        channel_id = cleaned_data.get("channel_id")

        if channel_name and channel_id:
            message = "Either specify channel name or User ID, not both"
            self.add_error("channel_name", message)
            self.add_error("channel_id", message)

        elif channel_name and not channel_name.startswith("#"):
            self.add_error("channel_name", 'Channel name should start with "#"')

        elif channel_name:
            channel_id = get_channel_id(channel_name)
            if channel_id is None:
                message = mark_safe(
                    "Slack channel name not found. <br>"
                    "You have to invite Slackbot to the channel if it's private, <br>"
                    "or you might just mistyped the channel name"
                )
                self.add_error("channel_name", message)
            else:
                cleaned_data["channel_id"] = channel_id

        elif channel_id and not channel_id.startswith("U"):
            self.add_error("channel_id", 'User ID should start with "U"')

        else:
            slack_api = slack.Api(config.BOT_ACCESS_TOKEN)
            res = slack_api.user_info(channel_id)
            if res is None:
                self.add_error("channel_id", "There is no such User ID")
            else:
                # I seriously don't understand which would be best to use
                # from the million kind of names Slack offers...
                cleaned_data["channel_name"] = (
                    "@" + res["user"]["profile"]["display_name"]
                )

        return cleaned_data


# We already got the channel_name and channel_id, we
# only need to check crontab syntax and gerrit query
class CrontabEditForm(CrontabFieldMixin, forms.ModelForm):
    class Meta:
        model = m.Crontab
        fields = ("gerrit_query", "crontab")
