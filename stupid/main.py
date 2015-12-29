import itertools
import logging
import time

import schedule

from stupid.chatbot import poll_broker
from stupid.fate import FateGameBot
from stupid.gohomebot import GoHomeBot
from stupid.lunchbot import LunchBot
from stupid.quotebot import QuoteBot
from stupid.slackbroker import SlackBroker


logger = logging.getLogger(__name__)


def main():
    # if len(sys.argv) > 1:
    #     if sys.argv[1] == 'read':
    #         ts = None
    #         if len(sys.argv) > 2:
    #             ts = float(sys.argv[2])
    #         sys.stdout.buffer.write(str(read_new_messages(ts)).encode('utf-8'))
    #         return 0
    setup_and_run()
    return 0


def setup_and_run():
    broker = SlackBroker()
    bots = [
        QuoteBot(broker),
        LunchBot(broker),
        FateGameBot(broker),
        GoHomeBot(broker),
    ]
    run_forever(broker, bots)


def run_forever(broker, bots):
    for i in itertools.count(0):
        for bot in bots:
            bot.run_pending()
        if i % 5 == 0:
            poll_broker(broker, bots)
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
