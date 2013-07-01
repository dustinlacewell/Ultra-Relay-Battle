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

    def on_hit(self, game):
    	if self.target.hp <= game.gametype.maxhealth:
    	    self.hit_msg(h=self.regenamt)
    	self.total_healing += self.regenamt
    	self.target.hp = min(
            self.target.hp + self.regenamt, 
            game.gametype.maxhealth,
        )
        return {'h':self.regenamt}

exported_class = RegenEffect
