from __future__ import unicode_literals

import itertools
import logging.config
import time

import schedule

from stupid.quotes import QuotesDatabase
from stupid.utils import weekday


CHANNEL_NAME = 'loud-launches'
CHANNEL_ID = 'C0G8JR6TE'  # channel_id(CHANNEL_NAME)
MY_ID = 'U0GN5LAQ3'
MY_USERNAME = 'Stupid'


logger = logging.getLogger('stupid')


def run_forever():
    for i in itertools.count(0):
        schedule.run_pending()
        if i % 600 == 0:
            logger.info('Iteration #%d', i)
            logger.info(render_jobs())
        time.sleep(1)


@weekday
def go_home():
    return post("Russian, go home", color='warning')


@weekday
def post_quote():
    registry = QuotesDatabase()
    quote = registry.get_random()
    post(">>>" + quote.text)
    registry.mark_as_shown(quote)


def render_jobs():
    return '\n'.join([
        str(job.next_run)
        for job in schedule.default_scheduler.jobs
    ])
