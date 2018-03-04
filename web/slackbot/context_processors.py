import secrets
from django.conf import settings
from constance import config
import slack


def slack_button(request):
    """Generates Slack url button for the administrator."""
    # Only superuser can install the app
    if not request.user.is_superuser:
        return {}

    # we don't need to calculate the slack_button_url if the bot is already configured
    if config.BOT_ACCESS_TOKEN != settings.BOT_ACCESS_TOKEN_DEFAULT:
        return {'is_bot_configured': True}

    # if the state is different we got from oauth authorization, we should refuse the token, because
    # probably a third-party generated it. For details, see https://api.slack.com/docs/slack-button
    request.session['oauth_state'] = secrets.token_urlsafe(32)
    slack_app = slack.App(config.SLACK_CLIENT_ID, config.SLACK_CLIENT_SECRET, config.SLACK_REDIRECT_URI)
    return {
        'slack_button_url': slack_app.make_button_url(request.session['oauth_state']),
        'is_bot_configured': False,
    }
