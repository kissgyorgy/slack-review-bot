import sqlite3
from typing import NamedTuple


class SlackToken(NamedTuple):
    channel: str
    channel_id: str
    webhook_url: str
    webhook_config_url: str
    access_token: str
    scope: str
    user_id: str
    team_name: str
    team_id: str


class Config(NamedTuple):
    # slack_token_id will be automatically determined
    gerrit_query: str
    crontab: str


class Database:
    def __init__(self):
        self._conn = sqlite3.connect('config.db')
        self._conn.row_factory = sqlite3.Row

    def close(self):
        self._conn.close()

    def init(self):
        with open('schema.sql', 'r') as f:
            self._conn.cursor().executescript(f.read())
        self._conn.commit()

    def load_config_old(self):
        import glob
        import json

        config = {}

        for fname in glob.glob('config/*.json'):
            print('Processing file', fname)
            with open(fname) as fp:
                channel_config = json.load(fp)
            channel = channel_config['slack']['incoming_webhook']['channel']
            config[channel] = channel_config

        return config

    def load_config(self):
        cur = self._conn.execute("""
            SELECT channel, gerrit_query, crontab
            FROM crontabs
            JOIN slack_tokens ON crontabs.slack_token_id = slack_tokens.id;
        """)
        return cur.fetchall()

    def save_config(self, slack_token, config):
        slack_query = """
            INSERT INTO slack_tokens(
                channel, channel_id, webhook_url, webhook_config_url, access_token, scope, user_id, team_name, team_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        config_query = "INSERT INTO crontabs (slack_token_id, gerrit_query, crontab) VALUES (?, ?, ?);"
        with self._conn:
            cur = self._conn.execute(slack_query, slack_token)
            self._conn.execute(config_query, (cur.lastrowid, *config))
