import datetime
import logging
import time

from stupid.chatbot import ChatBot, every_minute, trigger
from stupid.utils import weekday
from stupid.weather import WeatherForecast


logger = logging.getLogger(__name__)


class LunchBot(ChatBot):
    ASK_TIMEOUT = 15
    EXCLUDE = {
        "sobolevi": (datetime.datetime(2017, 8, 14), datetime.datetime(2017, 8, 26)),
        "mikhailzakharov": (datetime.datetime(2010, 1, 1), datetime.datetime(2020, 1, 1)),
        "deminp": (datetime.datetime(2017, 9, 15), datetime.datetime(2017, 10, 17)),
        "ivanchen": (datetime.datetime(2016, 7, 11), datetime.datetime(2016, 7, 25)),
    }

    def __init__(self, *args, **kwargs):
        super(LunchBot, self).__init__(*args, **kwargs)
        self.weather = WeatherForecast()
        self.schedule.every().day.at("11:55").do(self.eat_some)
        self.schedule.every().day.at("15:55").do(self.eat_some)
        self.announce_ts = None
        self.ask_for_reply_after = None
        self.users_to_ask = []

    @trigger
    def on_weather(self):
        return self.weather.report()

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

    @weekday
    def eat_some(self):
        response = self.broker.post(
            "Who is going to eat? Beware, it's {0}".format(self.weather.report()),
            color='warning',
        )
        logger.debug('Posted %r', response)
        self.announce_ts = float(response['message']['ts'])
        self.ask_for_reply_after = self.announce_ts + 60 * 3
        self.users_to_ask = self.dont_mention(self.users_on_channel())
        logger.debug('Scheduling ask_for_reply for %r after %r',
                     self.users_to_ask, self.ask_for_reply_after)

    def dont_mention(self, users):
        now = datetime.datetime.now()
        to_keep = set()
        for username in users.values():
            if username in self.EXCLUDE:
                if self.EXCLUDE[username][0] <= now < self.EXCLUDE[username][1]:
                    continue
            to_keep.add(username)
        return {k: v
                for k, v in users.items()
                if v in to_keep}

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
        replied_user_ids = {x.get('user') for x in self.broker.read_new_messages(self.announce_ts)}
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
