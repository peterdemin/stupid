import logging
import slack.channels
import slack.chat
from stupid.settings import SLACK_TOKEN


logger = logging.getLogger('stupid')


class SlackBroker(object):
    CHANNEL_NAME = 'loud-launches'
    CHANNEL_ID = 'C0G8JR6TE'  # channel_id(CHANNEL_NAME)
    MY_ID = 'U0GN5LAQ3'
    MY_USERNAME = 'Stupid'
    slack.api_token = SLACK_TOKEN

    def username(self, userid):
        return 'Petr'

    def messages(self):
        return []

    def post(self, message, color=None):
        logger.debug('Posting to %r message %r', self.CHANNEL_ID, message)
        if not color:
            return slack.chat.post_message(self.CHANNEL_ID, message, username='Stupid')
        else:
            return slack.chat.post_message(self.CHANNEL_ID, "", username='Stupid',
                                           attachments=[{'text': message, 'fallback': message, 'color': color}])

    def channel_info(self, name):
        for channel_info in slack.channels.list()['channels']:
            if channel_info['name'] == 'loud-launches':
                return channel_info

    def channel_id(self, name):
        return self.channel_info(name)['id']


    def user_name(self, user_id):
        return self.user_info(user_id)['name']


    def user_info(self, user_id):
        return slack.users.info(user_id)['user']


    def read_new_messages(self, oldest_ts=None):
        return slack.channels.history(self.CHANNEL_ID, oldest=oldest_ts)['messages']


# class Reader(object):
#     def __init__(self, handler):
#         self.handler = handler
#         self.oldest_ts = None
#
#     def read(self):
#         messages = read_new_messages(self.oldest_ts)
#         if messages:
#             for message in messages:
#                 if self.is_from_me(message):
#                     # Bot already replied, skip remaining messages
#                     logger.debug('Found own reply. Skipping older messages')
#                     break
#                 text = message['text']
#                 logger.debug('Parsing %s', text)
#                 if self.has_trigger(text):
#                     logger.debug('Triggering %r', self.handler)
#                     response = self.handler.on_message(text)
#                     if response is not None:
#                         post_response = post(response)
#                         if hasattr(self.handler, 'on_posted'):
#                             self.handler.on_posted(post_response['message'])
#             self.oldest_ts = messages[0]['ts']
#
#     def has_trigger(self, message):
#         msg = message.lower()
#         return '<@{0}>'.format(MY_ID) in message and any(trigger in msg for trigger in self.handler.triggers)
#
#     @staticmethod
#     def is_from_me(message):
#         return message.get('username', None) == MY_USERNAME
#
