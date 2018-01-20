import sys
import time
import json
import datetime as dt

import uwsgi
from croniter import croniter


def read_state():
    size = uwsgi.sharedarea_readlong(0, 0)
    state = uwsgi.sharedarea_read(0, 8, size)
    print('STATE', type(state), len(state))
    return json.loads(state)


def main():
    print('Started main')
    time.sleep(15)
    json_state = read_state()
    print('Shared state:', json_state)
    base = dt.datetime.now()
    # cron = croniter('0 9-18 * * mon-fri', base)
    cron = croniter('*/1 * * * *', base)
    print('Getting next_dt')
    next_dt = cron.get_next(dt.datetime)

    print('Starting cycle')
    while True:
        state = uwsgi.sharedarea_read(0, 0, 10)
        now = dt.datetime.now()
        rounded_now = now.replace(second=0, microsecond=0)
        if next_dt == rounded_now:
            next_dt = cron.get_next(dt.datetime)
            print('Stimmt, state:', read_state())
        print('Next', next_dt, 'now:', now)
        time.sleep(5)


if __name__ == '__main__':
    print('NAME IS MAIN')
    sys.exit(main())
