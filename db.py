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


class Crontab(NamedTuple):
    # slack_token_id will be automatically determined
    gerrit_query: str
    crontab: str


class Environment(NamedTuple):
    SLACK_CLIENT_ID: str
    SLACK_CLIENT_SECRET: str
    SECRET_KEY: str


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

    def load_environment(self):
        cur = self._conn.execute('SELECT * FROM environment')
        res = cur.fetchall()
        return Environment(**{r['name']: r['value'] for r in res})

    def load_crontabs(self):
        cur = self._conn.execute("""
            SELECT channel, gerrit_query, crontab
            FROM crontabs
            JOIN slack_tokens ON crontabs.slack_token_id = slack_tokens.id;
        """)
        return cur.fetchall()

    def save_crontab(self, slack_token, crontab):
        slack_insert = """
            INSERT INTO slack_tokens(
                channel, channel_id, webhook_url, webhook_config_url, access_token, scope, user_id, team_name, team_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        crontab_insert = "INSERT INTO crontabs (slack_token_id, gerrit_query, crontab) VALUES (?, ?, ?);"
        with self._conn:
            cur = self._conn.execute(slack_insert, slack_token)
            self._conn.execute(crontab_insert, (cur.lastrowid, *crontab))
