from random import randint, choice
from urb.effects import StatusEffect
from urb.util import render
class PoisonEffect(StatusEffect):

    name = 'poison'
    minticks = 5
    maxticks = 15
    minhits = 2
    maxhits = 5

    hit_msgs = [
	"{t}'s vision blurs.",
	"{t}'s stomach wrenchs in pain.",
	"{p}'s poison wrecks {t}'s insides.",
	"{t} vomits violently",
    ]

    wearoff_msgs = [
	"{t} is no longer poisoned.",
	"{t} is feeling a lot better.",
	"{t} shakes off his illness.",
	"{p}'s poison finally wears off {t}.",
    ]

    def __init__(self, app, source, move, target):
	super(PoisonEffect, self).__init__(app, source, move, target)

	self.total_damage = 0

	self.ticks = randint(self.minticks, self.maxticks)
	self.hits = randint(self.minhits, self.maxhits)

	self._ticks = 0
	self._hits = 0


    def random_hit_msg(self, dmg):
	return choice(self.hit_msgs).format(p=self.source, t=self.target)+ " [{0}]".format(dmg)

    def apply(self):
	super(PoisonEffect, self).apply()
	self.app.fsay("{t} has been poisoned!".format(t=self.target))

    def _get_wearoff_msg(self):
	return choice(self.wearoff_msgs).format(p=self.source, t=self.target)+ " [{0} tot]".format(self.total_damage)
    wearoff = property(_get_wearoff_msg)
    
    def tick(self):
	self._ticks += 1
	if self._ticks == self.ticks:
	    self._ticks = 0
	    self.ticks = randint(self.minticks, self.maxticks)
	    if self._hits == self.hits:
		self.app.fsay(self.wearoff)
		self.remove()
		return
	    else:
		self._hits += 1
		damage = randint(5, 30)
		self.total_damage += damage
		self.target.health -= damage
		if self.target.health <= 0:
		    self.app.fsay("{t} succumbs to {p}'s poison! [{d}]".format(p=self.source, t=self.target, d=damage))
		    death_msg = render(self.target.character.death_msg, self.target, self.source)
		    self.app.fsay(death_msg)
		    self.app.fsay("Death slaps a sticker on %s, \"Kaput!\", you're dead. [%d]" % (self.target, self.target.health))
		    winid = self.app.game.check_win_condition()
		    if winid != None:
			self.app.game.finish_battle(winid)            
                    self.remove()
		else:
		    self.app.fsay(self.random_hit_msg(damage))

exported_class = PoisonEffect
