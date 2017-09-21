import code
import itertools
import logging
import signal
import time
import traceback

from stupid.chatbot import poll_broker
from stupid.fate import FateGameBot
from stupid.lunchbot import LunchBot
from stupid.slackbroker import SlackBroker
from stupid.exitbot import ExitBot
from stupid.holidaybot import HolidayBot
# from stupid.rpcbot import RPCBot
# from stupid.quotebot import QuoteBot


logger = logging.getLogger(__name__)


def main():
    setup_and_run()
    return 0


def setup_and_run():
    bind_debug_signal()
    broker = SlackBroker()
    bots = [
        # QuoteBot(broker),
        # RPCBot(broker),
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
            except SystemExit:
                raise
            except:
                traceback.print_exc()
        if i % 3 == 0:
            try:
                poll_broker(i, broker, bots)
            except SystemExit:
                raise
            except:
                traceback.print_exc()
        if i % 1000 == 0:
            logger.info('Iteration #%d', i)
        time.sleep(1)


def debug(sig, frame):
    """
    Interrupt running process, and provide a python prompt for
    interactive debugging.
    """
    traceback.print_stack(frame)
    scope = {'_frame': frame}       # Allow access to frame object.
    scope.update(frame.f_globals)   # Unless shadowed by global
    scope.update(frame.f_locals)
    console = code.InteractiveConsole(scope)
    message = "Signal received: entering python shell.\nTraceback:\n"
    message += "".join(traceback.format_stack(frame))
    console.interact(message)
    logger.info("Finished debug session")


def bind_debug_signal():
    signal.signal(signal.SIGUSR1, debug)


if __name__ == '__main__':
    main()
