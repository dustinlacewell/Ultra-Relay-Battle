from random import randint, choice

from urb.effects.base_models import StatusEffect
from urb.util import render

class BlindEffect(StatusEffect):

    name = 'blind'
    verb = 'blinded'
    shorthand = 'BL'

    ticklimit = 15

    apply_msgs = [
	"{t} loses their vision completley!",
    ]

    remove_msgs = [
	"{t} regains their vision.",
	"{t} can once again see.",
	"{t} winces from the light as their vision returns.",
	"{t} shakes their head as their sight returns.",
    ]

exported_class = BlindEffect
