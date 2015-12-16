import datetime
import errno
import functools
import os
import sqlite3
import sys
import time
import urllib.request, urllib.error, urllib.parse

import schedule
import slack.chat
from bs4 import BeautifulSoup


CHANNEL = '#loud-launches'
oldest_message = None


def weekday(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if datetime.datetime.now().weekday() in range(0, 6):
            return func(*args, **kwargs)
    return wrapper


def post(message):
    return slack.chat.post_message(CHANNEL, message, username='Stupid')


def read_new_messages():
    slack.channels.history(CHANNEL, oldest_message)


@weekday
def eat_some():
    return post('Eat some!')


@weekday
def print_some():
    print('ok')


def print_jobs():
    for job in schedule.default_scheduler.jobs:
        print(job.next_run)


def main():
    slack.api_token = os.environ['STUPID_TOKEN']
    schedule.every().day.at("11:55").do(eat_some)
    schedule.every().day.at("15:55").do(eat_some)
    schedule.every().day.at("17:15").do(post, 'Go home')
    print_jobs()
    while True:
        schedule.run_pending()
        time.sleep(1)


def check():
    schedule.every().day.at("11:55").do(print_some)
    schedule.every().day.at("15:55").do(print_some)
    schedule.every().day.at("17:15").do(print_some)
    print_jobs()
    schedule.default_scheduler.run_all()



class Parser:
    db_file = "quotes.sqlite3"
    user_agent = (
        "Mozilla/5.0 "
        "(X11; Ubuntu; Linux x86_64; rv:30.0) "
        "Gecko/20100101 Firefox/30.0"
    )

    def __init__(self, start_page, end_page):
        self.start_page = start_page
        self.end_page = end_page
        self.db = sqlite3.connect(self.db_file)
        self.create_table()

    def create_table(self):
        cursor = self.db.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS quotes "
            "(id INTEGER, text TEXT, datetime INTEGER)"
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
        soup = BeautifulSoup(html)
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
            sys.stdout.write(
                "Skipping quote #%s as it is already in the DB\n"
                %
                quote["id"]
            )
            return
        dt = datetime.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M")
        timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
        cursor.execute(
            "INSERT INTO quotes (id, text, datetime) VALUES (?,?,?)",
            (quote["id"], quote["text"], timestamp)
        )
        self.db.commit()


def update_bash(start_page=0, end_page=10):
    if start_page > 0 and end_page >= start_page:
        p = Parser(start_page, end_page)
        p.parse_all_pages()
    else:
        sys.stderr.write("Please check the page numbers\n")
        sys.exit(errno.EINVAL)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            check()
            sys.exit(0)
        elif sys.argv[1] == 'bash':
            update_bash()
            sys.exit(0)
    main()
