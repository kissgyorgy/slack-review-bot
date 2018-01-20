import sys
import time
import glob
import json
import datetime as dt
from croniter import croniter


def load_config():
    config = {}

    for fname in glob.glob('config/*.json'):
        print('Processing file', fname)
        with open(fname) as fp:
            channel_config = json.load(fp)
        channel = channel_config['slack']['incoming_webhook']['channel']
        config[channel] = channel_config

    return config


def init_crontabs(config):
    crontabs = {}
    base = dt.datetime.now()
    for channel, conf in config.items():
        cron = croniter(conf['crontab'], base)
        next_dt = cron.get_next(dt.datetime)
        crontabs[channel] = [cron, next_dt]
    return crontabs


# def get_all_next_dts(crontabs):
#     for channel, cron in crontabs.items():
#         next_dt = cron.get_next(dt.datetime)
#         crontabs[channel][1] = next_dt
#     return crontabs


# def check_dts(crontabs, now):
#     for channel, cron, next_dt in crontabs.items():
#         if next_dt == rounded_now:


# def get_earliest_dt(crontabs):
#     next_dt = None
#     for channel, cron in crontabs.items():
#         current_dt = cron.get_next(dt.datetime)
#         if next_dt is None or current_dt < next_dt:
#             next_dt = current_dt
#             next_channel = channel

#     print('Earliest cron entry:', next_channel, next_dt)
#     return next_channel, next_dt


def main():
    print('Crontab started')
    config = load_config()
    print('Config:', config)
    crontabs = init_crontabs(config)
    # channel, next_dt = get_earliest_dt(crontabs)

    while True:
        now = dt.datetime.now()
        rounded_now = now.replace(second=0, microsecond=0)
        for channel, crontup in crontabs.items():
            cron, next_dt = crontup
            if next_dt == rounded_now:
                print('Sending now to', channel)
                next_dt = cron.get_next(dt.datetime)
                crontabs[channel][1] = next_dt
        # if next_dt == rounded_now:
            # channel, next_dt = get_earliest_dt(crontabs)
        print('Next', next_dt, 'now:', now)
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())
