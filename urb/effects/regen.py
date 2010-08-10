from random import randint, choice
from urb.effects import StatusEffect
from urb.util import render
class RegenEffect(StatusEffect):

    name = 'regen'
    tickslimit = 10
    hitslimit = 10
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
	"Wounds on {t}'s body heal.",
	"{t} is feeling better and better.",
	"A healing wave washes over {t}'s body.",
	"{t} is slightly regenerated.",
    ]

    def __init__(self, app, source, move, target):
	super(RegenEffect, self).__init__(app, source, move, target)

	self.total_health = 0

	self.ticks = self.tickslimit
	self.hits = self.hitslimit

	self._ticks = 0
	self._hits = 0


    def random_hit_msg(self, hp):
	return choice(self.hit_msgs).format(p=self.source, t=self.target)+ " [{0}]".format(hp)

    def tick(self):
	self._ticks += 1
	if self._ticks == self.ticks:
	    self._ticks = 0
	    if self._hits == self.hits:
		self.remove()
		return
	    else:
		self._hits += 1
		health = self.regenamt
		if self.target.health <= self.app.game.settings.maxhealth:
		    self.app.fsay(self.random_hit_msg(health))
		self.total_health += health
		self.target.health = min(self.target.health + health, self.app.game.settings.maxhealth)

exported_class = RegenEffect
