from random import randint, choice
from urb.effects.models import StatusEffect
from urb.players.models import Action
from urb.util import render

class StunEffect(StatusEffect):

    name = 'stun'
    verb = 'stunned'

    lowerticks = 5
    upperticks = 8

    apply_msgs = [
        "{t} has been knocked unconscious!",
    ]

    remove_msgs = [
        "{t} wakes up.",
        "{t} suddenly shakes awake.",
        "{t} returns to consciousness.",
        "{t} is no longer asleep",
    ]

    def apply(self):
        Action.objects.filter(player=self.target).delete()
        super(StunEffect, self).apply()

    def get_denial(self, move):
        return "You can't do '{m.fullname}' while you are {v}!".format(m=move, v=self.verb)

exported_class = StunEffect
