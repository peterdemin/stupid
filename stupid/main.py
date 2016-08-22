import itertools
import logging
import time
import traceback

import schedule

from stupid.chatbot import poll_broker
from stupid.fate import FateGameBot
from stupid.lunchbot import LunchBot
from stupid.quotebot import QuoteBot
from stupid.slackbroker import SlackBroker
from stupid.exitbot import ExitBot
from stupid.holidaybot import HolidayBot


logger = logging.getLogger(__name__)


def main():
    setup_and_run()
    return 0


def setup_and_run():
    broker = SlackBroker()
    bots = [
        QuoteBot(broker),
        LunchBot(broker),
        FateGameBot(broker),
        ExitBot(broker),
        HolidayBot(broker),
    ]
    run_forever(broker, bots)


def run_forever(broker, bots):
    for i in itertools.count(0):
        for bot in bots:
            try:
                bot.run_pending()
            except:
                traceback.print_exc()
        if i % 3 == 0:
            try:
                poll_broker(i, broker, bots)
            except:
                traceback.print_exc()
        if i % 600 == 0:
            logger.info('Iteration #%d', i)
            logger.info(render_jobs())
        time.sleep(1)


def render_jobs():
    return '\n'.join([
        str(job.next_run)
        for job in schedule.default_scheduler.jobs
    ])


if __name__ == '__main__':
    main()
