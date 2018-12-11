import bisect
from collections import OrderedDict

import datetime

from stupid.chatbot import ChatBot, trigger


# https://www.ca3.uscourts.gov/2019-federal-holidays
HOLIDAYS = OrderedDict([
    (datetime.date(2018, 1, 1), "New Year's Day"),
    (datetime.date(2018, 1, 15), "Birthday of Martin Luther King, Jr."),
    (datetime.date(2018, 2, 19), "Washington's Birthday"),
    (datetime.date(2018, 5, 28), "Memorial Day"),
    (datetime.date(2018, 7, 4), "Independence Day"),
    (datetime.date(2018, 9, 3), "Labor Day"),
    (datetime.date(2018, 10, 8), "Columbus Day"),
    (datetime.date(2018, 11, 12), "Veterans Day"),
    (datetime.date(2018, 11, 22), "Thanksgiving Day"),
    (datetime.date(2018, 12, 25), "Christmas Day"),

    (datetime.date(2019, 1, 1), "New Year's Day"),
    (datetime.date(2019, 1, 21), "Birthday of Martin Luther King, Jr."),
    (datetime.date(2019, 2, 18), "Washington’s Birthday"),
    (datetime.date(2019, 5, 27), "Memorial Day"),
    (datetime.date(2019, 7, 4), "Independence Day"),
    (datetime.date(2019, 9, 2), "Labor Day"),
    (datetime.date(2019, 10, 14), "Columbus Day"),
    (datetime.date(2019, 11, 11), "Veterans Day"),
    (datetime.date(2019, 11, 28), "Thanksgiving Day"),
    (datetime.date(2019, 12, 25), "Christmas Day"),
])


class HolidayBot(ChatBot):
    def __init__(self, *args, **kwargs):
        super(HolidayBot, self).__init__(*args, **kwargs)
        self.schedule.every().day.at('13:30').do(self.post_next_week_holiday)
        self.schedule.every().day.at('17:50').do(self.post_tomorrow_holiday)
        self.schedule.every().day.at('08:00').do(self.post_today_holiday)
        self.holiday_dates = list(HOLIDAYS.keys())
        self.holiday_titles = list(HOLIDAYS.values())

    @trigger
    def on_holiday(self):
        index = bisect.bisect_left(self.holiday_dates, datetime.date.today())
        hs = slice(index, index + 3)
        lines = [
            day.strftime('%A, %B %-d - {0}'.format(title))
            for day, title in zip(self.holiday_dates[hs], self.holiday_titles[hs])
        ]
        return '\n'.join(lines)

    def post_today_holiday(self):
        title = self.today_holiday()
        if title is not None:
            return self.broker.post("Happy {0}! It is day off.".format(title),
                                    color='warning')

    def post_tomorrow_holiday(self):
        title = self.tomorrow_holiday()
        if title is not None:
            return self.broker.post("Tomorrow is day off - {0}.".format(title),
                                    color='info')

    def post_next_week_holiday(self):
        day = datetime.date.today() + datetime.timedelta(days=7)
        title = self.holiday_title(day)
        if title is not None:
            return self.broker.post("On the next week {0} is day off - {1}"
                                    .format(day.strftime("%A, %B %-d"), title),
                                    color='info')

    def today_holiday(self):
        return self.holiday_title(datetime.date.today())

    def tomorrow_holiday(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        return self.holiday_title(tomorrow)

    def holiday_title(self, day):
        holiday_date, holiday_title = self.previous_holiday(day)
        if day == holiday_date:
            return holiday_title

    def previous_holiday(self, from_date):
        index = bisect.bisect_left(self.holiday_dates, from_date)
        try:
            return self.holiday_dates[index], self.holiday_titles[index]
        except IndexError:
            pass

    def next_holiday(self, from_date):
        index = bisect.bisect_right(self.holiday_dates, from_date)
        try:
            return self.holiday_dates[index], self.holiday_titles[index]
        except IndexError:
            pass
