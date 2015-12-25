import logging
import time

from schedule import Scheduler

from stupid.chatbot import ChatBot, every_minute
from stupid.utils import weekday
from stupid.weather import WeatherForecast


logger = logging.getLogger(__name__)


class LunchBot(ChatBot):
    ASK_TIMEOUT = 15

    def __init__(self, *args, **kwargs):
        super(LunchBot, self).__init__(*args, **kwargs)
        self.weather = WeatherForecast()
        self.schedule = Scheduler()
        self.schedule.every().day.at("11:55").do(self.eat_some)
        self.schedule.every().day.at("15:55").do(self.eat_some)
        self.announce_ts = None
        self.ask_for_reply_after = None
        self.users_to_ask = []

    @every_minute
    @weekday
    def on_timeout(self):
        if self.ask_for_reply_after is not None:
            delta = round((time.time() - self.ask_for_reply_after) / 60)
            disable = False
            if 0 <= delta < self.ASK_TIMEOUT:
                disable = self.ask_for_reply()
            if delta > self.ASK_TIMEOUT:
                logger.debug("Asking for reply timeout - %d - cancelling", delta)
                disable = True
            if disable:
                self.ask_for_reply_after = None
                self.users_to_ask = []
        else:
            self.schedule.run_pending()

    def eat_some(self):
        response = self.broker.post(
            "Who is going to eat? Beware, it's {0}"
            .format(self.weather.report()),
            color='warning',
        )
        logger.debug('Posted %r', response)
        self.announce_ts = float(response['message']['ts'])
        self.ask_for_reply_after = self.announce_ts + 60 * 3
        self.users_to_ask = self.users_on_channel()
        logger.debug('Scheduling ask_for_reply for %r after %r',
                     self.users_to_ask, self.ask_for_reply_after)

    def users_on_channel(self):
        return {user_id: self.username(user_id)
                for user_id in self.broker.channel_info(self.broker.CHANNEL_NAME)['members']
                if user_id != self.broker.MY_ID}

    def ask_for_reply(self):
        """
        Check if not all chatroom participants replied
        Ask for reply if found any.
        """
        logger.debug("Asking for reply")
        # Bot messages do not have 'user' field
        replied_user_ids = {x.get('user', None) for x in self.broker.read_new_messages(self.announce_ts)}
        logger.debug("Users replied after announcement: %r", replied_user_ids)
        if replied_user_ids.intersection(self.users_to_ask):
            # At least one user replied
            to_ask = set(self.users_to_ask).difference(replied_user_ids)
            if to_ask:
                for user_id in to_ask:
                    logger.debug("Asking %r", self.users_to_ask[user_id])
                    self.broker.post('@{0}, are you going to eat some?'.format(self.users_to_ask[user_id]))
                logger.debug('Looks like one reminder is enough... Canceling join')
            else:
                logger.debug('Everyone replied, canceling')
            return True
        logger.debug('Do not be first to reply to yourself, skipping')
        return False
