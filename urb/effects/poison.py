from random import randint, choice
from urb.effects.base_models import ActiveEffect
from urb.util import render

class PoisonEffect(ActiveEffect):

    name = 'poison'
    verb = 'poisoned'
    shorthand = 'PO'

    lowerticks = 5
    upperticks = 15
    lowerhits = 2
    upperhits = 5

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

    def on_hit(self, game):
        damage = randint(5, 30)
        self.total_damage += damage
        self.target.health -= damage
        self.save()
        self.target.save()
        return {'h':damage}

    def on_death(self):
        self.app.fsay("{t} succumbs to {p}'s poison! [{d}]".format(p=self.source, t=self.target, d=self.total_damage))

exported_class = PoisonEffect
