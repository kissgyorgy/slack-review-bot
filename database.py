import sqlite3
from typing import NamedTuple


class SlackToken(NamedTuple):
    id: int
    channel: str
    channel_id: str
    webhook_url: str
    webhook_config_url: str
    access_token: str
    scope: str
    user_id: str
    team_name: str
    team_id: str
    bot_user_id: str
    bot_access_token: str


class Crontab(NamedTuple):
    id: int
    gerrit_query: str
    crontab: str


class Environment(NamedTuple):
    SLACK_CLIENT_ID: str
    SLACK_CLIENT_SECRET: str
    SLACK_REDIRECT_URI: str
    SECRET_KEY: str
    GERRIT_URL: str


class Database:
    def __init__(self):
        self._conn = sqlite3.connect('config.db')
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.execute('PRAGMA foreign_keys = ON')

    def close(self):
        self._conn.close()

    def init(self):
        with open('schema.sql', 'r') as f:
            self._conn.cursor().executescript(f.read())
        self._conn.commit()

    def load_environment(self):
        cur = self._conn.execute('SELECT * FROM environment')
        res = cur.fetchall()
        return Environment(**{r['name']: r['value'] for r in res
                              if r['name'] in Environment._fields})

    def load_crontabs(self):
        cur = self._conn.execute("""
            SELECT crontabs.id crontab_id, crontab, gerrit_query, webhook_url, channel
            FROM crontabs JOIN slack_tokens
            ON crontabs.slack_token_id = slack_tokens.id;
        """)
        return cur.fetchall()

    def load_crontab(self, crontab_id):
        cur = self._conn.execute("""
            SELECT channel, gerrit_query, crontab
            FROM crontabs
            JOIN slack_tokens ON crontabs.slack_token_id = slack_tokens.id
            WHERE crontabs.id = ?;
        """, (crontab_id,))
        res = cur.fetchone()
        return res['channel'], res['gerrit_query'], res['crontab']

    def save_crontab(self, slack_token, crontab):
        slack_insert = """
            INSERT INTO slack_tokens(
                channel, channel_id, webhook_url, webhook_config_url, access_token, scope, user_id, team_name, team_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        crontab_insert = "INSERT INTO crontabs (slack_token_id, gerrit_query, crontab) VALUES (?, ?, ?);"
        with self._conn:
            cur = self._conn.execute(slack_insert, slack_token[1:])
            self._conn.execute(crontab_insert, (cur.lastrowid, *crontab[1:]))

    def delete(self, slack_token_id):
        with self._conn:
            # this will delete with CASCADE, so crontab entries belonging to this will be deleted also
            self._conn.execute('DELETE FROM slack_tokens WHERE id = ?', (slack_token_id,))

    def update_crontab(self, crontab):
        with self._conn:
            self._conn.execute('UPDATE crontabs SET gerrit_query = ?, crontab = ? WHERE id = ?',
                               (crontab.gerrit_query, crontab.crontab, crontab.id))

    def load_token_and_channel(self, crontab_id):
        with self._conn:
            cur = self._conn.execute("""
                SELECT access_token, channel, slack_tokens.id slack_token_id
                FROM slack_tokens
                JOIN crontabs ON crontabs.slack_token_id = slack_tokens.id
                WHERE crontabs.id = ?
            """, (crontab_id,))
        return cur.fetchone()
