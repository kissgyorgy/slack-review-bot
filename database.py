import sqlite3
from typing import NamedTuple


class Crontab(NamedTuple):
    id: int
    channel_name: str
    channel_id: str
    gerrit_query: str
    crontab: str


class SentMessage(NamedTuple):
    ts: str
    channel_id: str
    text: str


class Environment(NamedTuple):
    SLACK_CLIENT_ID: str
    SLACK_CLIENT_SECRET: str
    SLACK_REDIRECT_URI: str
    SECRET_KEY: str
    GERRIT_URL: str
    BOT_ACCESS_TOKEN: str


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
        return Environment(**{r['name']: r['value'] for r in res
                              if r['name'] in Environment._fields})

    def load_all_crontabs(self):
        cur = self._conn.execute('SELECT * FROM crontabs')
        return (Crontab(**r) for r in cur.fetchall())

    def load_crontab(self, crontab_id):
        cur = self._conn.execute('SELECT * FROM crontabs WHERE crontabs.id = ?;', (crontab_id,))
        res = cur.fetchone()
        return Crontab(**res)

    def save_crontab(self, crontab):
        crontab_insert = 'INSERT INTO crontabs (channel_name, channel_id, gerrit_query, crontab) VALUES (?, ?, ?, ?);'
        with self._conn:
            self._conn.execute(crontab_insert, crontab[1:])

    def update_crontab(self, crontab):
        with self._conn:
            self._conn.execute("""
                UPDATE crontabs SET channel_name = ?, channel_id = ?, gerrit_query = ?, crontab = ? WHERE id = ?
            """, (crontab.channel_name, crontab.channel_id, crontab.gerrit_query, crontab.crontab, crontab.id))

    def delete_crontab(self, crontab_id):
        with self._conn:
            self._conn.execute('DELETE FROM crontabs WHERE crontabs.id = ?', (crontab_id,))

    def load_sent_messages(self, slack_channel_id):
        cur = self._conn.execute('SELECT * FROM sent_messages WHERE sent_messages.channel_id = ?;', (slack_channel_id,))
        return (SentMessage(**r) for r in cur.fetchall())

    def save_sent_message(self, message):
        with self._conn:
            self._conn.execute('INSERT INTO sent_messages (ts, channel_id, text) VALUES (?, ?, ?);', message)

    def delete_sent_message(self, message):
        with self._conn:
            self._conn.execute('DELETE FROM sent_messages WHERE sent_messages.ts = ?', (message.ts,))
