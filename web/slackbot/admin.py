from django.contrib import admin
from .models import Crontab, SentMessage, ReviewRequest


class CrontabAdmin(admin.ModelAdmin):
    class Meta:
        model = Crontab


class SentMessageAdmin(admin.ModelAdmin):
    list_display = ("ts", "channel_id", "crontab")


class ReviewRequestAdmin(admin.ModelAdmin):
    list_display = ("gerrit_url", "channel_id", "crontab")


admin.site.register(Crontab, CrontabAdmin)
admin.site.register(SentMessage, SentMessageAdmin)
admin.site.register(ReviewRequest, ReviewRequestAdmin)
