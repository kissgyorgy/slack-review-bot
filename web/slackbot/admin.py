from django.contrib import admin
from .models import Crontab, SentMessage


admin.site.register(Crontab)
admin.site.register(SentMessage)
