import secrets
from flask import Flask, request, session, render_template, redirect, url_for, flash, g
from cronjob import init_crontabs
from croniter import croniter
import slack
from database import Database, SlackToken, Crontab


db = Database()
env = db.load_environment()
db.close()

app = Flask(__name__)
app.secret_key = env.SECRET_KEY

slack_app = slack.App(env.SLACK_CLIENT_ID, env.SLACK_CLIENT_SECRET, env.SLACK_REDIRECT_URI)


class Alert:
    PRIMARY = 'primary'
    SECONDARY = 'secondary'
    SUCCESS = 'success'
    DANGER = 'danger'
    WARNING = 'warning'
    INFO = 'info'
    LIGHT = 'light'
    DARK = 'dark'


@app.before_request
def before_request():
    g.db = Database()


@app.after_request
def after_request(response):
    g.db.close()
    return response


def _make_slack_button_url():
    # if the state is different we got from oauth authorization, we should refuse the token, because
    # probably a third-party generated it. For details, see https://api.slack.com/docs/slack-button
    session['oauth_state'] = secrets.token_urlsafe(32)
    return slack_app.make_button_url(session['oauth_state'])


def _get_channel():
    try:
        return session['webhook_data']['incoming_webhook']['channel']
    except KeyError:
        return None


@app.route('/')
def index():
    config = g.db.load_crontabs()

    return render_template('index.html',  # noqa
        config=config,
        crontabs=init_crontabs(config),
        has_unfinished_config='webhook_data' in session,
        unfinished_channel=_get_channel(),
        slack_button_url=_make_slack_button_url(),
    )


@app.route('/edit/<int:crontab_id>', methods=['GET', 'POST'])
def edit(crontab_id):
    channel, gerrit_query, crontab = g.db.load_crontab(crontab_id)

    if request.method == 'POST' and is_form_valid():
        gerrit_query = request.form['gerrit_query']
        crontab = request.form['crontab']
        g.db.update_crontab(crontab_id, Crontab(gerrit_query, crontab))
        flash('Updated succesfully.', Alert.SUCCESS)

    return render_template('edit.html', channel=channel, gerrit_query=gerrit_query, crontab=crontab,
                           crontab_id=crontab_id)


@app.route('/new', methods=['GET'])
def new():
    if 'webhook_data' not in session:
        return redirect(_make_slack_button_url())

    return render_template('new.html', channel=_get_channel(), invalid_form=session.get('invalid_form', None))


def is_form_valid():
    gerrit_query_data = request.form['gerrit_query']
    crontab_data = request.form['crontab']
    is_valid = True

    if not gerrit_query_data:
        flash('You need to have a gerrit query.', Alert.DANGER)
        # TODO: check if it doesn't give an error against Gerrit.
        is_valid = False

    if not crontab_data:
        flash('You need to fill out the crontab entry.', Alert.DANGER)
        is_valid = False

    elif not croniter.is_valid(crontab_data):
        flash('Invalid crontab syntax.', Alert.DANGER)
        is_valid = False

    return is_valid


@app.route('/new', methods=['POST'])
def save_new_to_db():
    if not is_form_valid():
        session['invalid_form'] = request.form
        return redirect(url_for('new'))

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
    crontab = Crontab(request.form['gerrit_query'], request.form['crontab'])
    g.db.save_crontab(slack_token, crontab)
    session.clear()
    flash(f'Config added for {slack_token.channel}', Alert.SUCCESS)
    return redirect('/')


@app.route('/delete-unfinished', methods=['POST'])
def delete_unfinished():
    res = slack.revoke_token(session['webhook_data']['access_token'])
    if not res.ok or not res.json()['ok']:
        flash('Unknown error revoking access token!', Alert.DANGER)
        return redirect('/')

    session.clear()
    flash(f'Deleted unfinished request for {_get_channel()}, you can add a new channel now.', Alert.WARNING)
    return redirect('/')


@app.route('/delete/<int:crontab_id>', methods=['POST'])
def delete_existing(crontab_id):
    access_token, channel, slack_token_id = g.db.load_token_and_channel(crontab_id)
    res = slack.revoke_token(access_token)
    if not res.ok or not res.json()['ok']:
        print(res.json())
        flash('Unknown error revoking access token!', Alert.DANGER)
        return redirect('/')

    g.db.delete(slack_token_id)
    flash(f'Succesfully removed bot from {channel}', Alert.SUCCESS)
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

    session['webhook_data'] = slack_app.request_oauth_token(request.args['code'])

    return redirect(url_for('new'))


@app.route('/usage')
def usage():
    return render_template('usage.html')
