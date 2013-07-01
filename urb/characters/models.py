import random

from django.db import models

from urb.fields import MultiSelectField
from urb.effects.choices import EFFECTS
from urb.characters.choices import (
    TARGET_TYPES, ELEMENTS,
    CHAR_STRINGS, MOVE_STRINGS
)

class Character(models.Model):
    selector = models.CharField(
        max_length = 16,
        unique=True,
    )

    name = models.CharField(
        max_length = 24,
    )

    pstrength = models.IntegerField(default=50)
    pdefense = models.IntegerField(default=50)
    mstrength = models.IntegerField(default=50)
    mdefense = models.IntegerField(default=50)

    weakness = models.CharField(
        max_length=32, choices=ELEMENTS,
    )

    resistance = models.CharField(
        max_length=32, choices=ELEMENTS,
    )

    apply_blind = models.BooleanField(default=False)
    apply_poison = models.BooleanField(default=False)
    apply_regen = models.BooleanField(default=False)
    apply_stun = models.BooleanField(default=False)

    finalized = models.BooleanField(default=False)

    def get_effects(self):
        effects = []
        for attr in [
            a for a in dir(self) 
            if a.startswith('apply_')]:
                val = getattr(self, attr)
                if val:
                    name = attr.split('_')[-1]
                    effects.append(name)
        return effects
    effects = property(get_effects)

    def _get_moves(self):
        return Move.objects.filter(character=self)
    moves = property(_get_moves)

    def _get_description(self):
        strings = self.characterstring_set.filter(type='description')
        if strings:
            return random.choice(strings)
        return "<<_get_description>>"
    description = property(_get_description)

    def _get_selection(self):
        strings = self.characterstring_set.filter(type='selection')
        if strings:
            return random.choice(strings)
        return "<<_get_selection>>"
    selection = property(_get_selection)

    def _get_block_begin(self):
        strings = self.characterstring_set.filter(type='blockbegin')
        if strings:
            return random.choice(strings)
        return "<<_get_block_begin>>"
    block_begin = property(_get_block_begin)

    def _get_block_fail(self):
        strings = self.characterstring_set.filter(type='blockfail')
        if strings:
            return random.choice(strings)
        return "<<_get_block_fail>>"
    block_fail = property(_get_block_fail)

    def _get_block_success(self):
        strings = self.characterstring_set.filter(type='blocksuccess')
        if strings:
            return random.choice(strings)
        return "<<_get_block_success>>"
    block_success = property(_get_block_success)

    def _get_resting(self):
        strings = self.characterstring_set.filter(type='resting')
        if strings:
            return random.choice(strings)
        return "<<_get_resting>>"
    resting = property(_get_resting)

    def _get_kill(self):
        strings = self.characterstring_set.filter(type='kill')
        if strings:
            return random.choice(strings)
        return "<<_get_kill>>"
    kill = property(_get_kill)

    def _get_fatality(self):
        strings = self.characterstring_set.filter(type='fatality')
        if strings:
            return random.choice(strings)
        return "<<_get_fatality>>"
    fatality = property(_get_fatality)

    def _get_death(self):
        strings = self.characterstring_set.filter(type='death')
        if strings:
            return random.choice(strings)
        return "<<_get_death>>"
    death = property(_get_fatality)

    def _get_taunt(self):
        strings = self.characterstring_set.filter(type='taunt')
        if strings:
            return random.choice(strings)
        return "<<_get_taunt>>"
    taunt = property(_get_taunt)

    def get_gauge(self, attribute):
        val = getattr(self, attribute, "????")
        bar = "*" * int(val / 10.0)
        filler = " " * (10 - len(bar))
        return "[%s%s]" % (bar, filler)

    def __str__(self):
        return self.selector

    vschema = { 
        'selector':'str', 
        'name':'msg', 
        'description':'msg',
        'selection':'msg', 
        'block_begin':'msg', 'block_fail':'msg', 'block_success':'msg', 
        'kill':'msg', 'fatality':'msg', 'death':'msg', 
        'taunt':'msg', 'resting':'msg',
        'pstrength':'int', 'pdefense':'int', 
        'mstrength':'int', 'mdefense':'int', 
        'weakness':'str', 'resistance':'str', 
        'finalized':'int'
    }

    vorder = ( 
        'selector', 'name', 
        'resistance', 'weakness',
        'pstrength', 'pdefense', 
        'mstrength', 'mdefense', 
        'description', 'selection', 
        'block_begin', 'block_fail', 'block_success', 
        'resting', 'taunt', 
        'kill', 'fatality', 'death', 
        'finalized'
    )

class CharacterString(models.Model):
    character = models.ForeignKey(Character)
    content = models.CharField(max_length = 64)
    type = models.CharField(max_length=32, choices=CHAR_STRINGS)


class Move(models.Model):
    selector = models.CharField(
        max_length = 16)

    name = models.CharField(
        max_length = 24)

    character = models.ForeignKey(
        Character, null=True, blank=True)

    target_type = models.CharField(max_length=16, choices=TARGET_TYPES,)

    element = models.CharField(
        max_length=32,
        choices=ELEMENTS,
    )

    power = models.IntegerField(default=100)

    can_super = models.BooleanField(default=False)
    can_counter = models.BooleanField(default=False)

    def _get_prepare(self):
        return random.choice(self.movestring_set.filter(type='prepare'))
    prepare = property(_get_prepare)

    def _get_super_prepare(self):
        return random.choice(self.movestring_set.filter(type='superprepare'))
    super_prepare = property(_get_super_prepare)

    def _get_hit(self):
        return random.choice(self.movestring_set.filter(type='hit'))
    hit = property(_get_hit)

    def _get_miss(self):
        return random.choice(self.movestring_set.filter(type='miss'))
    miss = property(_get_miss)

    def _get_critical_hit(self):
        return random.choice(self.movestring_set.filter(type='criticalhit'))
    critical_hit = property(_get_critical_hit)

    def _get_super_hit(self):
        return random.choice(self.movestring_set.filter(type='superhit'))
    super_hit = property(_get_super_hit)

    def _get_mpcost(self):
        return 300
    mpcost = property(_get_mpcost)

    def __str__(self):
        return self.selector

    def _info_str(self):
        return "(%s) %s : %d : %s : %s : %s %s" % (
                self.selector, self.name, self.power, 
                "???", "???",
                "CanSpr+" if self.can_super else "",
                "CanCtr+" if self.can_counter else "",
                )
    info = property(_info_str)

    vschema = {'selector':'str', 'name':'msg', 'character':'str',
        'power':'int', 'element':'element', 'target':'str', 'can_super':'int',
        'can_counter':'int', 'effectchances':'msg', 'prepare':'msg',
        'super_prepare':'msg', 'hit':'msg', 'miss':'msg',
        'critical_hit':'msg', 'super_hit':'msg'}

    vorder = ('selector', 'name', 'character', 'power', 'target',
        'element', 'can_super', 'can_counter', 'prepare', 'super_prepare',
        'hit', 'miss', 'critical_hit', 'super_hit', 'effectchances') 
    

class MoveString(models.Model):
    move = models.ForeignKey(Move)
    content = models.CharField(max_length = 64)
    type = models.CharField(max_length=32, choices=MOVE_STRINGS)

