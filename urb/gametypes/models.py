from django.db import models

from urb.gametypes.choices import GAMETYPES, GAMESTATES

class GameType(models.Model):
    selector = models.CharField(
        max_length = 16)

    full_name = models.CharField(
        max_length = 32)

    engine = models.CharField(max_length=64, choices=GAMETYPES)

    start_hp = models.IntegerField(default=500)
    start_mp = models.IntegerField(default=500)
    start_sp = models.IntegerField(default=0)

    max_hp = models.IntegerField(default=1000)
    max_mp = models.IntegerField(default=1000)
    max_sp = models.IntegerField(default=1000)

    max_sp_level = models.IntegerField(default=6)
    damage_multiplier = models.FloatField(default=1.0)
    mp_rate = models.IntegerField(default=3)

    vschema = {'start_hp':'int', 'start_mp':'int', 'start_sp':'int',
               'max_hp':'int', 'max_mp':'int', 'max_sp':'int',
               'max_sp_level':'int', 'damage_multiplier':'float', 'mp_rate':'int',
    }

    vorder = ('start_hp', 'start_mp', 'start_sp',
              'max_hp', 'max_mp', 'max_sp', 'max_sp_level',
              'damage_multiplier', 'mp_rate')       

    def __unicode__(self):
        return self.full_name

class GameRecord(models.Model):
    gametype = models.ForeignKey(GameType, null=True, blank=True)
    gametime = models.IntegerField(default=0)
    tickrate = models.FloatField(default=1.0)
    state = models.CharField(
        max_length=64, 
        choices=GAMESTATES, 
        default='selection'
    )

    def __unicode__(self):
        return u"%s (%s)" % (self.gametype, self.pk)

    def _get_players(self):
        from urb.players.models import Player
        return Player.objects.filter(game=self)
    players = property(_get_players)

    
