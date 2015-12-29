from __future__ import unicode_literals

import logging.config
import random
import sqlite3
from collections import namedtuple

import requests
from bs4 import BeautifulSoup
from six import text_type


logger = logging.getLogger('stupid.quotes')
Quote = namedtuple('Quote', ('id', 'text', 'shown'))


class BashOrgScrapper(object):
    def is_valid(self, soup):
        center_tags = soup.find_all("center")
        # Page validity check
        for center in center_tags:
            if center.contents[0] == "Invalid page.":
                return False
        return True

    def top(self):
        response = requests.get("http://bash.org/?top2")
        return self.scrap(response.text)

    def scrap(self, html):
        soup = BeautifulSoup(html, "html.parser")
        if self.is_valid(soup):
            container = soup.find_all("center")[1].find_all("table")[0]
            # Get the stats for all of the quotes
            quotes_stat = container.find_all("p", {"class": "quote"})
            # Get the contents for all of the quotes
            quotes_content = container.find_all("p", {"class": "qt"})
            return map(self.parse_quote, quotes_stat, quotes_content)

    def parse_quote(self, stat, content):
        quote_idx = int(stat.find_all("a")[0].contents[0].getText().lstrip('#'))
        # votes = stat.find_all("font")[0].getText()
        lines = [row.replace("\r", "").replace("\n", "").strip()
                 for row in content
                 if text_type(row) != "<br/>"]
        return Quote(quote_idx, '\n'.join(filter(None, lines)), False)


class QuotesDatabase(object):
    db_file = "quotes.sqlite3"

    def __init__(self):
        self.db = sqlite3.connect(self.db_file)
        self.create_table()

    def add(self, quote):
        same_id_quotes = self.cursor.execute(
            "SELECT * FROM quotes WHERE id=?",
            (quote.id,)
        ).fetchall()
        if len(same_id_quotes):
            logger.debug("Skipping quote #%s as it is already in the DB",
                         quote.id)
            return
        self.cursor.execute(
            "INSERT INTO quotes (id, text, shown) VALUES (?,?,?)",
            (quote.id, quote.text, False)
        )
        self.db.commit()

    def get_random(self):
        return self.fetch(self.random_unshown_id())

    def create_table(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS quotes "
            "(id INTEGER, text TEXT, shown BOOLEAN)"
        )
        self.db.commit()

    def fetch(self, quote_id):
        return Quote(*self.cursor.execute("SELECT id, text, shown FROM quotes WHERE id=?", quote_id).fetchone())

    def random_unshown_id(self):
        ids = self.cursor.execute("SELECT id FROM quotes WHERE shown=0").fetchall()
        return random.choice(ids)

    def mark_as_shown(self, quote):
        self.cursor.execute("UPDATE quotes SET shown=1 WHERE id=?", (str(quote.id),))

    @property
    def cursor(self):
        return self.db.cursor()


def update_bash():
    db = QuotesDatabase()
    for quote in BashOrgScrapper().top():
        db.add(quote)


if __name__ == '__main__':
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
    update_bash()
