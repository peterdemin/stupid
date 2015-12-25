import inspect
import logging


logger = logging.getLogger(__name__)


def trigger(method):
    method.is_trigger = True
    return method


class ChatBot(object):
    triggers = {}

    def on_message(self, message):
        if not self.triggers:
            self.introspect()
        text = message['text'].lower()
        for trigger in self.triggers:
            if trigger in text:
                return self.triggers[trigger](self)

    def username(self, userid):
        return 'Petr'

    def game_messages(self):
        return []

    @classmethod
    def introspect(cls):
        for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
            if name.startswith('on_'):
                if getattr(method, 'is_trigger', False) is True:
                    event_name = name[3:]
                    cls.triggers[event_name] = method


class Reader(object):
    def __init__(self, handler):
        self.handler = handler
        self.oldest_ts = None

    def read(self):
        messages = read_new_messages(self.oldest_ts)
        if messages:
            for message in messages:
                if self.is_from_me(message):
                    # Bot already replied, skip remaining messages
                    logger.debug('Found own reply. Skipping older messages')
                    break
                text = message['text']
                logger.debug('Parsing %s', text)
                if self.has_trigger(text):
                    logger.debug('Triggering %r', self.handler)
                    response = self.handler.on_message(text)
                    if response is not None:
                        post_response = post(response)
                        if hasattr(self.handler, 'on_posted'):
                            self.handler.on_posted(post_response['message'])
            self.oldest_ts = messages[0]['ts']

    def has_trigger(self, message):
        msg = message.lower()
        return '<@{0}>'.format(MY_ID) in message and any(trigger in msg for trigger in self.handler.triggers)

    @staticmethod
    def is_from_me(message):
        return message.get('username', None) == MY_USERNAME
