import time
import schedule
from . import scb_best


def run_jobs():
    scb_best.make_schedule()

    while True:
        schedule.run_pending()
        time.sleep(1)
