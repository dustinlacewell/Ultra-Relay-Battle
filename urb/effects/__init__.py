from random import randint, choice

from urb import imports

def refresh( context_name ):
    return imports.refresh(context_name)

def get( context_name ):
    return imports.get('effects', context_name)

class StatusEffect(object):

    name = None

    def __init__(self, app, source, move, target):
	self.app = app 
	self.source = source
	self.move = move 
	self.target = target
	self.apply()

    def apply(self):
	print "POISON APPLY"
	self.target.effects[self.name] = self

    def remove(self):
	print "POISON REMOVED"
	if self.name in self.target.effects:
	    del self.target.effects[self.name]	

    def tick(self):
	self.remove()
