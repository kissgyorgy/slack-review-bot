import secrets
# import uwsgi
from flask import Flask, request, session, render_template, redirect, url_for, flash, g
from cronjob import init_crontabs
import slack
from db import Database, SlackToken, Crontab


class Alert:
    PRIMARY = 'primary'
    SECONDARY = 'secondary'
    SUCCESS = 'success'
    DANGER = 'danger'
    WARNING = 'warning'
    INFO = 'info'
    LIGHT = 'light'
    DARK = 'dark'


# FIXME?
db = Database()
env = db.load_environment()
db.close()

app = Flask(__name__)
app.secret_key = env.SECRET_KEY


@app.before_request
def before_request():
    g.db = Database()


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route('/')
def index():
    config = g.db.load_crontabs()
    crontabs = init_crontabs(config)

    # if the state is different we got from oauth authorization, we should refuse the token, because
    # probably a third-party generated it. For details, see https://api.slack.com/docs/slack-button
    session['oauth_state'] = secrets.token_urlsafe(32)
    slack_button_url = slack.make_button_url(env, session['oauth_state'])

    if 'webhook_data' in session:
        has_unfinished_config = True
        unfinished_channel = session['webhook_data']['incoming_webhook']['channel']
    else:
        has_unfinished_config = False
        unfinished_channel = None

    return render_template('index.html', config=config, crontabs=crontabs, oauth_state=session['oauth_state'],
                           has_unfinished_config=has_unfinished_config, unfinished_channel=unfinished_channel,
                           slack_button_url=slack_button_url)


@app.route('/edit')
def edit():
    return render_template('edit.html')


@app.route('/new', methods=['GET'])
def new():
    if 'webhook_data' not in session:
        session['oauth_state'] = secrets.token_urlsafe(32)
        slack_button_url = slack.make_button_url(env, session['oauth_state'])
        return redirect(slack_button_url)
    return render_template('new.html', channel=session['webhook_data']['incoming_webhook']['channel'])


@app.route('/new', methods=['POST'])
def save_to_db():
    wd = session['webhook_data']
    slack_token = SlackToken(
        wd['incoming_webhook']['channel'],
        wd['incoming_webhook']['channel_id'],
        wd['incoming_webhook']['url'],
        wd['incoming_webhook']['configuration_url'],
        wd['access_token'],
        wd['scope'],
        wd['user_id'],
        wd['team_name'],
        wd['team_id'],
    )
    crontab = Crontab('bla', '*/1 * * * *')
    g.db.save_crontab(slack_token, crontab)
    session.clear()
    flash(f'Config added for {slack_token.channel}', Alert.SUCCESS)
    return redirect('/')


@app.route('/delete-unfinished', methods=['POST'])
def delete_unfinished():
    res = slack.revoke_token(session['webhook_data']['access_token'])
    if not res.ok or not res.json()['ok']:
        flash('Unknown error revoking access token!', Alert.DANGER)
        redirect('/')

    channel = session['webhook_data']['incoming_webhook']['channel']
    session.clear()
    flash(f'Deleted unfinished request for {channel}, you can add a new channel now.', Alert.WARNING)
    return redirect('/')


@app.route('/slack-oauth')
def slack_oauth():
    # If the states don't match, the request come from a third party and the process should be aborted.
    # See https://api.slack.com/docs/slack-button
    if request.args['state'] != session['oauth_state']:
        return 'Invalid state. You have been logged and will be caught.'

    error = request.args.get('error')
    if error == 'access_denied':
        flash('Access denied - Request cancelled', Alert.WARNING)
        return redirect('/')
    elif error is not None:
        flash('Unknown error - try again', Alert.DANGER)
        return redirect('/')

    webhook_data = slack.request_oauth_token(env, request.args['code'])
    session['webhook_data'] = webhook_data

    return redirect(url_for('new'))
