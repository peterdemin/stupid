import logging
import slack.channels
import slack.groups
import slack.chat
from stupid.settings import SLACK_TOKEN


logger = logging.getLogger('stupid')


class SlackBroker(object):
    CHANNEL_NAME = 'loud-launches'
    CHANNEL_ID = 'G0J9HTX1S'  # channel_id(CHANNEL_NAME)
    MY_ID = 'U0GN5LAQ3'
    MY_USERNAME = 'Stupid'
    slack.api_token = SLACK_TOKEN

    def __init__(self):
        self.oldest_ts = None

    def post(self, message, color=None):
        logger.debug('Posting to %r message %r', self.CHANNEL_ID, message)
        if not color:
            return slack.chat.post_message(self.CHANNEL_ID, message, username='Stupid')
        else:
            return slack.chat.post_message(self.CHANNEL_ID, "", username='Stupid',
                                           attachments=[{'text': message, 'fallback': message, 'color': color}])

    def channel_info(self, name):
        for channel_info in slack.channels.list()['channels']:
            if channel_info['name'] == name:
                return channel_info

    def channel_id(self, name):
        return self.channel_info(name)['id']

    def username(self, userid):
        return self.user_name(userid)

    def user_name(self, user_id):
        return self.user_info(user_id)['name']

    def user_info(self, user_id):
        return slack.users.info(user_id)['user']

    def messages(self, oldest_ts=None):
        return self.read_new_messages(oldest_ts)

    def read_new_messages(self, oldest_ts=None):
        return slack.groups.history(self.CHANNEL_ID, oldest=oldest_ts)['messages']

    def poll_channel(self):
        messages = self.read_new_messages(self.oldest_ts)
        if messages:
            self.oldest_ts = messages[0]['ts']
            for message in messages:
                if self.is_from_me(message):
                    # Bot already replied, skip remaining messages
                    logger.debug('Found own reply. Skipping older messages')
                    break
                yield message

    def is_from_me(self, message):
        return message.get('username') == self.MY_USERNAME
