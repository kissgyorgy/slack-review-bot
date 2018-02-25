from flask import Flask
from database import Database
import slack


db = Database()
env = db.load_environment()
db.close()

app = Flask(__name__)
app.secret_key = env.SECRET_KEY

slack_app = slack.App(env.SLACK_CLIENT_ID, env.SLACK_CLIENT_SECRET, env.SLACK_REDIRECT_URI)
slack_api = slack.Api(env.BOT_ACCESS_TOKEN)


class Alert:
    PRIMARY = 'primary'
    SECONDARY = 'secondary'
    SUCCESS = 'success'
    DANGER = 'danger'
    WARNING = 'warning'
    INFO = 'info'
    LIGHT = 'light'
    DARK = 'dark'


from . import views
