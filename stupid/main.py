import sys
from stupid import (
    schedule,
    Reader,
    eat_some,
    go_home,
    post_quote,
    run_forever,
    read_new_messages,
)
from stupid.fate import FateGame


def setup_and_run():
    schedule.every().day.at("11:55").do(eat_some)
    schedule.every().day.at("15:55").do(eat_some)
    schedule.every().day.at("17:15").do(go_home)
    schedule.every().day.at("9:25").do(post_quote)
    reader = Reader(FateGame)
    schedule.every(10).seconds.do(reader.read)
    run_forever()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'read':
            ts = None
            if len(sys.argv) > 2:
                ts = float(sys.argv[2])
            sys.stdout.buffer.write(str(read_new_messages(ts)).encode('utf-8'))
            return 0
    setup_and_run()
    return 0


if __name__ == '__main__':
    main()
