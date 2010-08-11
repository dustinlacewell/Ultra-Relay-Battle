from random import randint, choice
from urb.effects import StatusEffect
from urb.util import render

class PoisonEffect(StatusEffect):

    name = 'poison'
    verb = 'poisoned'
    shorthand = 'PO'

    minticks = 5
    maxticks = 15
    minhits = 2
    maxhits = 5

    apply_msgs = [
        "{t} has been poisoned!",
    ]

    remove_msgs = [
        "{t} is no longer poisoned.",
        "{t} is feeling a lot better.",
        "{t} shakes off his illness.",
        "{p}'s poison finally wears off. {t}.",
    ]

    hit_msgs = [
        "{t}'s vision blurs. [{h}]",
        "{t}'s stomach wrenchs in pain. [{h}]",
        "{p}'s poison wrecks {t}'s insides. [{h}]",
        "{t} vomits violently. [{h}]",
    ]

    def __init__(self, app, source, move, target):
        super(PoisonEffect, self).__init__(app, source, move, target)

        self.total_damage = 0

        self.ticklimit = randint(self.minticks, self.maxticks)
        self.hitlimit = randint(self.minhits, self.maxhits)

    def oh_hit(self):
        damage = randint(5, 30)
        self.total_damage += damage
        self.target.health -= damage
        return {'h':damage}

    def on_death(self):
        self.app.fsay("{t} succumbs to {p}'s poison! [{d}]".format(p=self.source, t=self.target, d=self.total_damage))

exported_class = PoisonEffect
