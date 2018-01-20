import datetime as dt
import schedule
from balabit_config import BalabitConfigBase
import slack


class Config(BalabitConfigBase):
    CHANNEL = '#scb-best'
    QUERY = 'ownerin:scb-best+AND+status:open+AND+NOT+label:Code-Review=2'
    WEBHOOK_URL = 'https://hooks.slack.com/services/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'


def print_something():
    print(f'I ran at {dt.datetime.now()}')


def make_schedule():
    schedule.every().seconds.do(print_something)
    for hour in range(9, 19):
        hour = f'{hour}:00'
        schedule.every().monday.at(hour).do(print_something)
        schedule.every().tuesday.at(hour).do(print_something)
        schedule.every().wednesday.at(hour).do(print_something)
        schedule.every().thursday.at(hour).do(print_something)
        schedule.every().friday.at(hour).do(print_something)
