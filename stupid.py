import datetime
import errno
import functools
import itertools
import logging.config
import os
import random
import sqlite3
import sys
import time
import urllib.request
from collections import namedtuple

import schedule
import slack.channels
import slack.chat
from bs4 import BeautifulSoup


CHANNEL_NAME = 'loud-launches'
CHANNEL_ID = 'C0G8JR6TE'  # channel_id(CHANNEL_NAME)
slack.api_token = os.environ.pop('STUPID_TOKEN')


logger = logging.getLogger('stupid')


def main():
    schedule.every().day.at("11:55").do(eat_some)
    schedule.every().day.at("15:55").do(eat_some)
    schedule.every().day.at("17:15").do(post, 'Go home')
    schedule.every().day.at("9:30").do(post_quote)
    run_forever()


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
        if datetime.datetime.now().weekday() in range(0, 6):
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


@weekday
def eat_some():
    users = {user_id: user_name(user_id)
             for user_id in channel_info(CHANNEL_NAME)['members']}
    announce_ts = time.time()
    logger.debug('Scheduling ask_for_reply for %r after %r',
                 users, announce_ts)
    schedule.every().minute.do(
        ask_for_reply,
        users=users,
        announce_ts=announce_ts,
    )
    return post('Eat some!')


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
    registry = Quotes()
    quote = registry.get_random_quote()
    post(quote.text)  # .text.encode('utf-8'))
    registry.mark_as_shown(quote)


def render_jobs():
    return '\n'.join([
        str(job.next_run)
        for job in schedule.default_scheduler.jobs
    ])


class Quotes:
    db_file = "quotes.sqlite3"
    user_agent = (
        "Mozilla/5.0 "
        "(X11; Ubuntu; Linux x86_64; rv:30.0) "
        "Gecko/20100101 Firefox/30.0"
    )
    Quote = namedtuple('Quote', ('id', 'text', 'date', 'shown'))

    def __init__(self, start_page=None, end_page=None):
        self.start_page = start_page
        self.end_page = end_page
        self.db = sqlite3.connect(self.db_file)
        self.create_table()

    def create_table(self):
        cursor = self.db.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS quotes "
            "(id INTEGER, text TEXT, datetime INTEGER, shown BOOLEAN)"
        )
        self.db.commit()

    def get_url(self, page_number):
        return "http://bash.im/index/%s" % page_number

    def fetch_page(self, page_number):
        req = urllib.request.Request(
            url=self.get_url(page_number),
            headers={"User-Agent": self.user_agent}
        )
        f = urllib.request.urlopen(req)
        return f.read()

    def parse_all_pages(self):
        for page_number in range(self.start_page, self.end_page + 1):
            self.parse_quotes(page_number)

    def parse_quotes(self, page_number):
        html = self.fetch_page(page_number)
        soup = BeautifulSoup(html, "html.parser")
        quote_divs = soup.find_all("div", class_="quote")
        for quote_div in quote_divs:
            quote = {}
            text_div = quote_div.find("div", class_="text")
            # Skipping advertisement
            if not text_div:
                continue
            # The quote text divs contain strings of text and
            # <br/> elements that can be skipped. Joining the
            # text strings using \n as separator results in
            # the quote text with line breaks preserved.
            quote["text"] = "\n".join(
                [x for x in text_div.contents if isinstance(x, str)]
            )
            actions_div = quote_div.find("div", class_="actions")
            quote["datetime"] = actions_div.find(
                "span",
                class_="date"
            ).contents[0]
            quote["id"] = actions_div.find(
                "a",
                class_="id"
            ).contents[0][1:]
            self.write_quote(quote)

    def write_quote(self, quote):
        cursor = self.db.cursor()
        same_id_quotes = cursor.execute(
            "SELECT * FROM quotes WHERE id=?",
            (quote["id"],)
        ).fetchall()
        if len(same_id_quotes):
            logger.debug("Skipping quote #%s as it is already in the DB",
                         quote["id"])
            return
        dt = datetime.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M")
        timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
        cursor.execute(
            "INSERT INTO quotes (id, text, datetime, shown) VALUES (?,?,?,?)",
            (quote["id"], quote["text"], timestamp, False)
        )
        self.db.commit()

    def get_random_quote(self):
        cursor = self.db.cursor()
        ids = cursor.execute("SELECT id FROM quotes WHERE shown=0").fetchall()
        the_id = random.choice(ids)
        row = cursor.execute("SELECT * FROM quotes WHERE id=?", the_id).fetchone()
        # import pdb; pdb.set_trace()  # XXX BREAKPOINT
        return self.Quote(*row)

    def mark_as_shown(self, quote):
        cursor = self.db.cursor()
        cursor.execute("UPDATE quotes SET shown=1 WHERE id=?", (str(quote.id),))


def update_bash(start_page=1, end_page=10):
    if start_page > 0 and end_page >= start_page:
        Quotes(start_page, end_page).parse_all_pages()
    else:
        sys.stderr.write("Please check the page numbers\n")
        sys.exit(errno.EINVAL)


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


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'bash':
            update_bash()
            sys.exit(0)
        elif sys.argv[1] == 'read':
            ts = None
            if len(sys.argv) > 2:
                ts = float(sys.argv[2])
            sys.stdout.buffer.write(str(read_new_messages(ts)).encode('utf-8'))
            sys.exit(0)
    main()
