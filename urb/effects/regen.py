from random import randint, choice
from urb.effects import StatusEffect
from urb.util import render

class RegenEffect(StatusEffect):

    name = 'regen'
    verb = 'regenerating'
    shorthand = 'RG'

    ticklimit = 10
    hitlimit = 10
    regenamt = 10

    apply_msgs = [
        "{t} starts to regenerate!",
    ]

    remove_msgs = [
	"{t} stops regenerating.",
	"{t}'s body is no longer regenerating.",
	"{t}'s regen wears off",
    ]

    hit_msgs = [
	"Wounds on {t}'s body heal. [{h}]",
	"{t} is feeling better and better. [{h}]",
	"A healing wave washes over {t}'s body. [{h}]",
	"{t} is slightly regenerated. [{h}]",
    ]

    def __init__(self, app, source, move, target):
	super(RegenEffect, self).__init__(app, source, move, target)
	self.total_health = 0

    def on_hit(self):
	if self.target.health <= self.app.game.settings.maxhealth:
	    self.random_hit_msg(h=self.regenamt)
	self.total_health += self.regenamt
	self.target.health = min(self.target.health + self.regenamt, self.app.game.settings.maxhealth)
        return {'h':self.regenamt}

exported_class = RegenEffect
