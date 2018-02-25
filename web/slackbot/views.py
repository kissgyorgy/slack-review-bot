from django.views import generic
from .models import Crontab


class HomeView(generic.ListView):
    model = Crontab
    context_object_name = 'crontabs'
    template_name = 'home.html'


class UsageView(generic.TemplateView):
    template_name = 'usage.html'


class NewCrontabView(generic.CreateView):
    model = Crontab
    fields = ('channel_name', 'gerrit_query', 'crontab')
    template_name = 'crontab_form.html'
    success_url = '/'
