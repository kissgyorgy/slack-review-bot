from django.contrib import admin
from .models import Crontab, SentMessage


class CrontabAdmin(admin.ModelAdmin):
    class Meta:
        model = Crontab


class SentMessageAdmin(admin.ModelAdmin):
    list_display = ("ts", "channel_id", "crontab")


admin.site.register(Crontab, CrontabAdmin)
admin.site.register(SentMessage, SentMessageAdmin)
