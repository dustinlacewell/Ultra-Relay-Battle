from random import randint, choice

from django.db import models

from urb.effects.choices import EFFECTS

class BaseEffect(models.Model):
    name = None
    verb = None
    shorthand = None

    apply_msgs = []
    remove_msgs = []

    ticklimit = None
    upperticks = None
    lowerticks = None

    type = models.CharField(max_length=32)
    ticks = models.IntegerField()
    maxticks = models.IntegerField(null=True, blank=True)
    source = models.ForeignKey(Player)
    move = models.ForeignKey(Move)
    target = models.ForeignKey(Player)
    total_damage = models.IntegerField(default=0)
    total_healing = models.IntegerField(default=0)

    def apply_msg(self, game, **kwargs):
        kwargs.update({
            'p': self.source,
            'm': self.move,
            't': self.target,
        })
        msg = choice(self.apply_msgs)
        msg = msg.format(**kwargs)
        game.app.fsay(msg)

    def remove_msg(self, game, **kwargs):
        kwargs.update({
            'p': self.source,
            'm': self.move,
            't': self.target,
        })
        msg = choice(self.remove_msgs)
        msg = msg.format(**kwargs)
        game.app.fsay(msg)

    def hit_msg(self, game, **kwargs):
        kwargs.update({
            'p': self.source,
            'm': self.move,
            't': self.target,
        })
        msg = choice(self.hit_msgs)
        msg = msg.format(**kwargs)
        game.app.fsay(msg)

    def apply(self, game):
        self.apply_msg(p=self.source, m=self.move, t=self.target)

    def remove(self, game):
        self.remove_msg(p=self.source, m=self.move, t=self.target)
        self.delete()

    def tick(self, game):
        self.ticks += 1
        if self.maxticks and self.ticks >= self.maxticks:
            self.remove(game)
        else:
            self.save()

    def __init__(self, *args, **kwargs):
        self._meta.get_field('type').default = self.name
        if self.upperticks is not None and self.lowerticks is not None:
            ticks = randint(self.minticks, self.maxticks)
            self._meta.get_field('maxticks').default = ticks
        elif self.ticklimit is not None:
             self._meta.get_field('maxticks').default = self.ticklimit
        super(StatusEffect, self).__init__(*args, **kwargs)    

    class Meta:
        abstract = True


class StatusEffect(BaseEffect): pass

class ActiveEffect(BaseEffect):

    remove_msgs = []

    ticklimit = 1

    hitlimit = None
    upperhits = None
    lowerhits = None

    hits = models.IntegerField(default=0)
    maxhits = models.IntegerField(null=True, blank=True)

    def on_hit(game): pass

    def on_death(game): pass

    def tick(self, game):
        self.ticks += 1
        if self.ticks % self.maxticks == 0:
            self.hits += 1
            if self.hits > self.hitlimit:
                self.remove(game)
            else:
                self.on_hit(game)
                if self.target.hp <= 0:
                    self.on_death(game)
                self.save()            

    def __init__(self, *args, **kwargs):
        if self.upperhits is not None and self.lowerhits is not None:
            hits = randint(self.minhits, self.maxhits)
            self._meta.get_field('maxhits').default = hits
        elif self.hitlimit is not None:
            self._meta.get_field('maxhits').default = self.hitlimit
        super(ActiveEffect, self).__init__(*args, **kwargs)    

