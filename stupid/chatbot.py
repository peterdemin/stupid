import inspect
import logging

from schedule import Scheduler


logger = logging.getLogger(__name__)


def trigger(method):
    method.is_trigger = True
    return method


def every_minute(method):
    method.every_minute = True
    return method


class ChatBot(object):
    def __init__(self, broker=None):
        self.schedule = Scheduler()
        self.triggers = {}
        self.pollers = []
        self.introspect()
        self.setup_pollers()
        self.broker = broker
        if self.broker is not None:
            self.username = self.broker.username
            self.messages = self.broker.messages

    def on_message(self, message):
        text = message['text'].lower()
        for trigger in self.triggers:
            if trigger in text:
                return self.triggers[trigger]()

    def setup_pollers(self):
        for poller in self.pollers:
            self.schedule.every().minute.do(poller)

    def run_pending(self):
        self.schedule.run_pending()

    def introspect(self):
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith('on_'):
                if getattr(method, 'is_trigger', False) is True:
                    event_name = name[3:]
                    self.triggers[event_name] = method
                if getattr(method, 'every_minute', False) is True:
                    self.pollers.append(method)
