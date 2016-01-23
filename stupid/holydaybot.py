import bisect
from collections import OrderedDict

import datetime

from stupid.chatbot import ChatBot


# http://dchr.dc.gov/page/holyday-schedules
HOLYDAYS = OrderedDict([
    (datetime.date(2016, 1, 1), "New Year's Day"),
    (datetime.date(2016, 1, 18), "Martin Luther King Jr. Day"),
    (datetime.date(2016, 2, 15), "Washington's Birthday"),
    (datetime.date(2016, 4, 15), "DC Emancipation Day"),
    (datetime.date(2016, 5, 30), "Memorial Day"),
    (datetime.date(2016, 7, 4), "Independence Day"),
    (datetime.date(2016, 9, 5), "Labor Day"),
    (datetime.date(2016, 10, 10), "Columbus Day"),
    (datetime.date(2016, 11, 11), "Veterans Day"),
    (datetime.date(2016, 11, 24), "Thanksgiving Day"),
    (datetime.date(2016, 12, 26), "Christmas Day"),
    (datetime.date(2017, 1, 16), "Inauguration Day"),
    (datetime.date(2017, 1, 2), "New Year's Day"),
    (datetime.date(2017, 1, 20), "Martin Luther King Jr. Day"),
    (datetime.date(2017, 2, 20), "Washington's Birthday"),
    (datetime.date(2017, 4, 17), "DC Emancipation Day"),
    (datetime.date(2017, 5, 29), "Memorial Day"),
    (datetime.date(2017, 7, 4), "Independence Day"),
    (datetime.date(2017, 9, 4), "Labor Day"),
    (datetime.date(2017, 10, 9), "Columbus Day"),
    (datetime.date(2017, 11, 10), "Veterans Day"),
    (datetime.date(2017, 11, 23), "Thanksgiving Day"),
    (datetime.date(2017, 12, 25), "Christmas Day"),
])


class HolydayBot(ChatBot):
    def __init__(self, *args, **kwargs):
        super(HolydayBot, self).__init__(*args, **kwargs)
        self.schedule.every().day.at('13:30').do(self.post_next_week_holyday)
        self.schedule.every().day.at('17:50').do(self.post_tomorrow_holyday)
        self.schedule.every().day.at('08:00').do(self.post_today_holyday)
        self.holyday_dates = list(HOLYDAYS.keys())
        self.holyday_titles = list(HOLYDAYS.values())

    def post_today_holyday(self):
        title = self.today_holyday()
        if title is not None:
            return self.broker.post("Happy {0}! It is day off.".format(title),
                                    color='warning')

    def post_tomorrow_holyday(self):
        title = self.tomorrow_holyday()
        if title is not None:
            return self.broker.post("Tomorrow is day off - {0}.".format(title),
                                    color='info')

    def post_next_week_holyday(self):
        day = datetime.date.today() + datetime.timedelta(days=7)
        title = self.holyday_title(day)
        if title is not None:
            return self.broker.post("On the next week {0} is day off - {1}."
                                    .format(day.strftime("%A, %B %-d"), title),
                                    color='info')

    def today_holyday(self):
        return self.holyday_title(datetime.date.today())

    def tomorrow_holyday(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        return self.holyday_title(tomorrow)

    def holyday_title(self, day):
        holyday_date, holyday_title = self.previous_holyday(day)
        if day == holyday_date:
            return holyday_title

    def previous_holyday(self, from_date):
        index = bisect.bisect_left(self.holyday_dates, from_date)
        return self.holyday_dates[index], self.holyday_titles[index]

    def next_holyday(self, from_date):
        index = bisect.bisect_right(self.holyday_dates, from_date)
        return self.holyday_dates[index], self.holyday_titles[index]
