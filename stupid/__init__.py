import datetime
import functools
import hashlib
import itertools
import logging.config
import os
import random
import re
import time

import requests
import schedule
import slack.channels
import slack.chat

from stupid.quotes import QuotesDatabase


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


def weekday(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if datetime.datetime.now().weekday() in range(0, 5):
            return func(*args, **kwargs)
    return wrapper


def post(message):
    logger.debug('Posting to %r message %r', CHANNEL_ID, message)
    return slack.chat.post_message(CHANNEL_ID, message, username='Stupid')


def channel_info(name):
    for channel_info in slack.channels.list()['channels']:
        if channel_info['name'] == 'loud-launches':
            return channel_info


def channel_id(name):
    return channel_info(name)['id']


def user_name(user_id):
    return user_info(user_id)['name']


def user_info(user_id):
    return slack.users.info(user_id)['user']


def read_new_messages(oldest_ts=None):
    return slack.channels.history(CHANNEL_ID, oldest=oldest_ts)['messages']


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


@weekday
def go_home():
    return post('Russian, go home')


@weekday
def eat_some():
    users = {user_id: user_name(user_id)
             for user_id in channel_info(CHANNEL_NAME)['members']
             if user_id != MY_ID}
    response = post("Eat some! But be aware: it's {0}".format(weather.report()))
    logger.debug('Posted %r', response)
    announce_ts = float(response['message']['ts'])
    logger.debug('Scheduling ask_for_reply for %r after %r',
                 users, announce_ts)
    schedule.every().minute.do(
        ask_for_reply,
        users=users,
        announce_ts=announce_ts,
    )


def ask_for_reply(users, announce_ts):
    attempt_number = round((time.time() - announce_ts) / 60)
    if attempt_number <= 15:
        logger.debug("Asking for reply #%d", attempt_number)
        # Bot messages do not have 'user' field
        replied_user_ids = {x.get('user', None) for x in read_new_messages(announce_ts)}
        logger.debug("Users replied after announcement: %r", replied_user_ids)
        if replied_user_ids.intersection(users):
            # At least one user replied
            to_ask = set(users).difference(replied_user_ids)
            if to_ask:
                for user_id in to_ask:
                    logger.debug("Asking %r", users[user_id])
                    post('@{0}, are you going to eat some?'.format(users[user_id]))
                logger.debug('Looks like one reminder is enough... Canceling join')
                return schedule.CancelJob
            else:
                logger.debug('Everyone replied, canceling join')
                return schedule.CancelJob
        else:
            logger.debug('Do not be first to reply to yourself, skipping')
            return None
    else:
        logger.debug("Asking for reply timeout - %d - cancelling", attempt_number)
        return schedule.CancelJob


@weekday
def post_quote():
    registry = QuotesDatabase()
    quote = registry.get_random()
    post(quote.text)
    registry.mark_as_shown(quote)


def render_jobs():
    return '\n'.join([
        str(job.next_run)
        for job in schedule.default_scheduler.jobs
    ])


class WeatherForecast(object):
    def __init__(self, token=None):
        self.token = token

    def report(self, latitude=38.9977, longitude=-77.0988):
        data = self.currently(latitude, longitude)
        return "{0:.0f} \u00B0F at {1:.1f} mph wind".format(
            data['apparentTemperature'],
            data['windSpeed'],
        )

    def currently(self, latitude, longitude):
        return self.forecast(latitude, longitude).json()['currently']

    def forecast(self, latitude, longitude):
        url = 'https://{url}/{token}/{latitude:.4f},{longitude:.4f}'.format(
            url='api.forecast.io/forecast',
            token=self.token,
            latitude=latitude,
            longitude=longitude,
        )
        logger.debug("Fetching %r", url)
        response = requests.get(url)
        logger.debug("Result %r", response.status_code)
        return response


class FateGame(object):
    current_game = None
    triggers = 'fate', 'done'
    good_bye = ("{0}\nYou can check target number by executing following code:\n"
                "python -c 'import hashlib; print(hashlib.md5(\"{0}\".encode(\"utf-8\")).hexdigest()[:6])'")
    re_numbers = re.compile(r'\b\d+\b')

    def __init__(self):
        self.invitation_time = None
        self.setup_game()

    @staticmethod
    def start():
        FateGame.current_game = FateGame()
        return FateGame.current_game

    @staticmethod
    def on_message(message):
        if 'done' in message:
            if FateGame.current_game is not None:
                result = FateGame.current_game.compose_result()
                FateGame.current_game = None
                return result
        elif 'fate' in message:
            return FateGame.start().invitation

    def compose_result(self):
        result = self.verifier
        winner = self.winner_username()
        if winner:
            result = '\n'.join([winner, result])
        return self.good_bye.format(result)

    def winner_username(self):
        if self.invitation_time is not None:
            bets = {}
            for message in read_new_messages(self.invitation_time):
                if Reader.is_from_me(message):
                    # Bot already replied, skip remaining messages
                    logger.debug('Found own reply. Skipping older messages')
                    break
                numbers = self.re_numbers.findall(message['text'])
                if numbers and message['user'] not in bets:
                    bets[message['user']] = abs(int(numbers[-1]) - self.winner_nbr)
            if bets:
                user_id, user_bet = sorted(bets.items(), key=lambda a: a[1])[0]
                return 'The winner is {0} with his bet {1}'.format(user_name(user_id), user_bet)

    @staticmethod
    def on_posted(message):
        if FateGame.current_game is not None:
            FateGame.current_game.invitation_time = message['ts']

    def setup_game(self):
        self.game_id = random.randint(1, 9999)
        self.winner_nbr = random.randint(1, 100)
        self.verifier = 'Fate game #{0} target number: {1}'.format(self.game_id, self.winner_nbr)

    @property
    def invitation(self):
        verifier_hash = self.easy_hash(self.verifier)
        return ("Everyone picks a number between 1 and 100.\n"
                "Then target number is posted.\n"
                "The one, who picked number closest to target wins\n"
                "Verification hash for this game is {0}".format(verifier_hash))

    def easy_hash(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]


logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'stupid': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
})


slack.api_token = os.environ.pop('STUPID_TOKEN')
weather = WeatherForecast(os.environ.pop('STUPID_WEATHER_TOKEN'))
