import datetime
import functools
import os
import sys
import time

import schedule
import slack.chat


def weekday(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if datetime.datetime.now().weekday() in range(0, 6):
            return func(*args, **kwargs)
    return wrapper


def post(message):
    return slack.chat.post_message('#loud-launches', message, username='Stupid')


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


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            check()
            sys.exit(0)
    main()
