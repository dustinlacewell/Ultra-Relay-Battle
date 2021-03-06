from random import randint, choice

from urb import imports

def refresh( context_name ):
    return imports.refresh(context_name)

def get( context_name ):
    return imports.get('effects', context_name)

class StatusEffect(object):

    name = None

    apply_msgs = []
    remove_msgs = []

    ticklimit = 0

    def __init__(self, app, source, move, target):
	self.app = app 
	self.source = source
	self.move = move 
	self.target = target
	self.apply()

    def apply(self):
        self.ticks = 0
	self.target.effects[self.name] = self
	self.app.fsay(choice(self.apply_msgs).format(p=self.source, m=self.move, t=self.target))

    def remove(self):
	if self.name in self.target.effects:
	    del self.target.effects[self.name]
	    self.app.fsay(choice(self.remove_msgs).format(p=self.source, m=self.move, t=self.target))

    def tick(self):
        self.ticks += 1
        if self.ticks >= self.ticklimit:
            self.remove()

class ActiveEffect(StatusEffect):

    hit_msgs = []

    hitlimit = 0

    def __init__(self, app, source, move, target):
        super(ActiveEffect, self).__init__(app, source, move, target)
        
        self.hits = 0

    def tick(self):
        self.ticks += 1
        if self.ticks % self.ticklimit == 0:
            if self.hits >= self.hitlimit:
                self.remove()
            else:
                self.hits += 1
                self.on_hit()
            
