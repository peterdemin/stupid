import datetime
import errno
import logging
import logging.config
import random
import sqlite3
import sys
from collections import namedtuple

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger('stupid.quotes')


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
        return requests.get(
            self.get_url(page_number),
            headers={"User-Agent": self.user_agent}
        ).text

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
                [x for x in text_div.contents if isinstance(x, basestring)]
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


if __name__ == '__main__':
    update_bash()
