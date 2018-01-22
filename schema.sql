PRAGMA FOREIGN_KEYS = ON;

CREATE TABLE slack_tokens (
  id INTEGER PRIMARY KEY,
  channel TEXT,
  channel_id TEXT,
  webhook_url TEXT,
  webhook_config_url TEXT,
  access_token TEXT,
  scope TEXT,
  user_id TEXT,
  team_name TEXT,
  team_id TEXT
);


CREATE TABLE crontabs (
  id INTEGER PRIMARY KEY,
  slack_token_id INTEGER,
  gerrit_query TEXT,
  crontab TEXT,
  FOREIGN KEY(slack_token_id) REFERENCES slack_tokens(id)
);
