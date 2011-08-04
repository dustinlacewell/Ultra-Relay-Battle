from random import randint, choice
from urb.effects import StatusEffect
from urb.util import render

class StunEffect(StatusEffect):

    name = 'stun'
    verb = 'stunned'

    minticks = 5
    maxticks = 8

    apply_msgs = [
        "{t} has been knocked unconscious!",
    ]

    remove_msgs = [
        "{t} wakes up.",
        "{t} suddenly shakes awake.",
        "{t} returns to consciousness.",
        "{t} is no longer asleep",
    ]

    def __init__(self, app, source, move, target):
        super(StunEffect, self).__init__(app, source, move, target)
        self.ticklimit = randint(self.minticks, self.maxticks)

    def apply(self):
        if self.target.current_move:
            self.target.current_move.alive = False
            self.target.current_move = None
        super(StunEffect, self).apply()

    def get_denial(self, move):
        return "You can't do '{m.fullname}' while you are {v}!".format(m=move, v=self.verb)

exported_class = StunEffect
