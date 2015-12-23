from __future__ import unicode_literals

import datetime
import functools
import itertools
import logging.config
import os
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


def post(message, color=None):
    logger.debug('Posting to %r message %r', CHANNEL_ID, message)
    if not color:
        return slack.chat.post_message(CHANNEL_ID, message, username='Stupid')
    else:
        return slack.chat.post_message(CHANNEL_ID, "", username='Stupid',
                                       attachments=[{'text': message, 'fallback': message, 'color': color}])


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
    return post("Russian, go home", color='warning')


@weekday
def eat_some():
    users = {user_id: user_name(user_id)
             for user_id in channel_info(CHANNEL_NAME)['members']
             if user_id != MY_ID}
    response = post("Eat some! But be aware: it's {0}".format(weather.report()), color='warning')
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
    post(">>>" + quote.text)
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
