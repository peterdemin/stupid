import datetime
import time

import schedule
from errbot import BotPlugin


CHANNEL_ID = 'C0G8JR6TE'  # channel_id(CHANNEL_NAME)
CHANNEL_NAME = 'loud-launches'


class Remainder(BotPlugin):
    def my_callback(self):
        if datetime.datetime.now().weekday() in range(0, 5):
            schedule.run_pending()

    def activate(self):
        super(Remainder, self).activate()
        for room in self.rooms():
            if room.name == CHANNEL_NAME:
                self.the_room = room
        schedule.every().day.at("11:55").do(self.eat_some)
        schedule.every().day.at("15:55").do(self.eat_some)
        schedule.every().day.at("17:15").do(self.post, 'Go home')
        self.start_poller(5, self.my_callback)
        self.eat_some()

    def post(self, message):
        return self.send(
            user=self.the_room,
            message_type='groupchat',
            text=message,
        )

    def eat_some(self):
        import pdb; pdb.set_trace()  # noqa
        occupants = self.the_room.occupants
        self.log.debug(occupants)
        return
        users = {user_id: user_name(user_id)
                 for user_id in channel_info(CHANNEL_ID)['members']}
        response = post("Eat some! But be aware: it's {0}".format(weather.report()))
        self.log.debug('Posted %r', response)
        announce_ts = float(response['message']['ts'])
        self.log.debug('Scheduling ask_for_reply for %r after %r',
                       users, announce_ts)

    def ask_for_reply(self, users, announce_ts):
        attempt_number = round((time.time() - announce_ts) / 60)
        if attempt_number <= 15:
            self.log.debug("Asking for reply #%d", attempt_number)
            # Bot messages do not have 'user' field
            replied_user_ids = {x.get('user', None) for x in read_new_messages(announce_ts)}
            self.log.debug("Users replied after announcement: %r", replied_user_ids)
            if replied_user_ids.intersection(users):
                # At least one user replied
                to_ask = set(users).difference(replied_user_ids)
                if to_ask:
                    for user_id in to_ask:
                        self.log.debug("Asking %r", users[user_id])
                        post('@{0}, are you going to eat some?'.format(users[user_id]))
                    self.log.debug('Looks like one reminder is enough... Canceling join')
                    return schedule.CancelJob
                else:
                    self.log.debug('Everyone replied, canceling join')
                    return schedule.CancelJob
            else:
                self.log.debug('Do not be first to reply to yourself, skipping')
                return None
        else:
            self.log.debug("Asking for reply timeout - %d - cancelling", attempt_number)
            return schedule.CancelJob
