PRAGMA FOREIGN_KEYS = ON;


CREATE TABLE crontabs (
  id INTEGER PRIMARY KEY,
  channel_name TEXT,
  channel_id TEXT,
  gerrit_query TEXT,
  crontab TEXT
);


CREATE TABLE environment (
  name TEXT UNIQUE,
  value TEXT
);


CREATE TABLE sent_messages (
  crontab_id INTEGER,
  ts TEXT PRIMARY KEY,
  channel_id TEXT,
  text TEXT,
  FOREIGN KEY(crontab_id) REFERENCES crontabs(id)
);
