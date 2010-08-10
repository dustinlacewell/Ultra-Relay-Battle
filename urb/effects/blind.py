from random import randint, choice

from urb.effects import StatusEffect
from urb.util import render

class BlindEffect(StatusEffect):

    name = 'regen'
    tickslimit = 15

    apply_msgs = [
	"{t} loses there vision completley!",
    ]

    remove_msgs = [
	"{t} regains their vision.",
	"{t} can once again see.",
	"{t} winces from the light as their vision returns.",
	"{t} shakes their head as their sight returns.",
    ]

    def __init__(self, app, source, move, target):
	super(BlindEffect, self).__init__(app, source, move, target)
	self._ticks = 0

    def apply(self):
	super(BlindEffect, self).apply()
	self.app.fsay(

    def tick(self):
	self._ticks += 1
	if self._ticks == self.tickslimit:
		self.remove()

exported_class = BlindEffect
