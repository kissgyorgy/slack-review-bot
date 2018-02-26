from django.contrib import admin
from .models import Crontab, SentMessage


class CrontabAdmin(admin.ModelAdmin):
    readonly_fields = ('channel_id',)

    class Meta:
        model = Crontab


admin.site.register(Crontab, CrontabAdmin)
admin.site.register(SentMessage)
