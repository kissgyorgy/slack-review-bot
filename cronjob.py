import sys
import time
from pprint import pprint
import datetime as dt
from croniter import croniter
from db import Database


def init_crontabs(config):
    crontabs = {}
    base = dt.datetime.now()
    for _, channel, _, crontab in config:
        cron = croniter(crontab, base)
        next_dt = cron.get_next(dt.datetime)
        crontabs[channel] = [cron, next_dt]
    return crontabs


def main():
    db = Database()
    print('Crontab started')
    config = db.load_crontabs()
    print('Loaded config:')
    pprint(config)
    crontabs = init_crontabs(config)

    while True:
        now = dt.datetime.now()
        rounded_now = now.replace(second=0, microsecond=0)
        for channel, crontup in crontabs.items():
            cron, next_dt = crontup
            if next_dt == rounded_now:
                print('Sending now to', channel)
                next_dt = cron.get_next(dt.datetime)
                crontabs[channel][1] = next_dt
                # TODO: handle 404; https://api.slack.com/docs/slack-button
        print('Next', next_dt, 'now:', now)
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())
