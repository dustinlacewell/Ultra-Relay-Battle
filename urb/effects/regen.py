from random import randint, choice
from urb.effects import StatusEffect
from urb.util import render
class RegenEffect(StatusEffect):

    name = 'regen'
    tickslimit = 10
    hitslimit = 10
    regenamt = 10

    hit_msgs = [
	"Wounds on {t}'s body heal.",
	"{t} is feeling better and better.",
	"A healing wave washes over {t}'s body.",
	"{t} is slightly regenerated.",
    ]

    wearoff_msgs = [
	"{t} stops regenerating.",
	"{t}'s body is no longer regenerating.",
	"{t}'s regen wears off",
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

    def apply(self):
	super(RegenEffect, self).apply()
	self.app.fsay("{t} starts to regenerate!".format(t=self.target))

    def _get_wearoff_msg(self):
	return choice(self.wearoff_msgs).format(p=self.source, t=self.target)+ " [{0} tot]".format(self.total_health)
    wearoff = property(_get_wearoff_msg)
    
    def tick(self):
	self._ticks += 1
	if self._ticks == self.ticks:
	    self._ticks = 0
	    if self._hits == self.hits:
		self.app.fsay(self.wearoff)
		self.remove()
		return
	    else:
		self._hits += 1
		if self.target.health >= self.app.game.settings.maxhealth:
		    self.app.fsay(self.random_hit_msg(health))
		health = self.regenamt
		self.total_health += health
		self.target.health = min(self.target.health + health, self.app.game.settings.maxhealth)

exported_class = RegenEffect
