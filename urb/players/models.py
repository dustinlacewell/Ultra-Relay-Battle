from django.db import models
from django.contrib.auth.models import AbstractUser

from urb.characters.models import Character, Move
from urb.gametypes.models import GameRecord
from urb.gametypes.choices import BUILTINS

class Team(models.Model):
    name = models.CharField(max_length=16)
    game = models.ForeignKey(GameRecord)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.game.pk)

class Player(AbstractUser):
    linewidth = 80

    game = models.ForeignKey(GameRecord, null=True, blank=True)
    team = models.ForeignKey(
        Team, null=True, blank=True)
    character = models.ForeignKey(
        Character, null=True, blank=True)

    hp = models.IntegerField(default=0)
    mp = models.IntegerField(default=0)
    sp = models.IntegerField(default=0)
        
    def __str__(self):
        return self.username
    
    def __unicode__(self):
        return self.username
    
    def __repr__(self):
        return self.username
    
    def __hash__(self):
        return hash(self.username)
    
    def __eq__(self, obj):
        return hash(self.username) == hash(obj)

    def __get_username__(self):
        return self.username
    name = property(__get_username__)
        
    def _status_msg(self):
        """Generate in-game status message"""
        action = "READY"
        if self.action:
            if self.action.target:
                action = "doing %s" % (self.action, )
            else:
                action = "doing '%s'" % (self.action.move.name, )
        return "%s is %s : %dHP : %dMP : %dSP" % (self.nickname, action, 
                                                  self.health, 
                                                  self.magicpoints, 
                                                  self.superpoints)
    status_msg = property(_status_msg)
    
    def _get_actions(self):
        """Return a boolean whether play is ready."""
        return Action.objects.filter(_alive=True, player=self)
    actions = property(_get_actions)
    
    def halt(self):
        if self.ready:
            self.tell("You're not doing anything yet!")
        else:
            self.app.fsay("%s stops doing '%s'." % (self.nickname, self.current_move.name))
            self.action.alive = False
            self.current_move = None
            self.app.fsay(self.status_msg) 
            
    def is_enemy(self, player):
        return player.team != self.team
    
    def has(self, effectname):
        return effectname in self.effects
            
class Action(models.Model):
    alive = models.BooleanField(default=True)
    ticksleft = models.IntegerField(default=10)
    move = models.ForeignKey(Move)
    super = models.IntegerField(default=0)
    builtin = models.CharField(
        max_length=32,
        choices=BUILTINS,
        null=True,
        blank=True,
    )
    player = models.ForeignKey(Player)
    target = models.ForeignKey(
        Player, null=True, blank=True, related_name='hostile_actions')

    def __unicode__(self):
        return u"'%s' on '%s'" % (self.move.name, self.target.name)
