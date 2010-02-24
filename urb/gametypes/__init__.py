import random

from urb import imports
from urb.util import dlog, dtrace
from urb import validation
from urb.validation import ValidationError

from urb.constants import *

class GameType(object):
    def __init__(_self, self):
        pass
    def on_setup(_self, self):
        pass
    
    def on_prep_player(_self, self, nickname):
        if nickname in self.fighters:
            theplayer = self.fighters[nickname]
            theplayer.character = None
            theplayer.current_move = "unready"
            theplayer.health = self.settings.starthealth
            theplayer.magicpoints = self.settings.startmagic
            theplayer.superpoints = self.settings.startsuper
            theplayer.team = self.next_team_id
            self.next_team_id += 1
            
            theplayer.session.switch('prebattle')    
            
    def on_close_selection(_self, self):
        if self.state == "selection":
            for nick, player in self.app.game.fighters.iteritems():
                char = player.character.fullname if player.character else "NO CHAR"
                self.app.signals['game_msg'].emit(
                "%s(%s) - %d HP : %d MP : %d SP %s" % (
                nick, char,  player.health, 
                player.magicpoints, player.superpoints, ": READY" if player.ready else ""))
            if len(self.get_ready()) == len(self.fighters):
                self.app.signals['global_msg'].emit(
                "# Character Selection is now closed.")
                self.state = "prebattle"
            else:
                self.app.signals['game_msg'].emit(
                "##    Waiting for all players to READY.   ##")
                unready = self.get_unready()
                for theplayer in unready:
                    self.app.tell(theplayer.nickname,
                        "!! Battle is waiting on you to, 'ready' !!")
            
                        
    def on_battle_start(_self, self):
        if self.state == "prebattle":
            unready = self.get_unready()
            for theplayer in unready:
                nickname = theplayer.nickname
                self.app.signals['game_msg'].emit(
                "%s was dropped from the battle." % nickname)
                self.on_forfeit(nickname)
                self.app.tell(nickname,
                "You were dropped from battle for not being ready.")
            for nickname, theplayer in self.fighters.iteritems():
                theplayer.session.switch('battle')
            self.app.signals['game_msg'].emit(
            "****  BATTLE HAS BEGUN ****")
            self.tick_timer.start(self.tickrate)
        
    def on_battle_pause(_self, self):
        pass
        
    def on_battle_resume(_self, self):
        pass
        
    def on_battle_abort(_self, self):
        self.tick_timer.stop()
        self.actions = []
        self.app.signals['game_msg'].emit(
        "**** BATTLE HAS BEEN ABORTED ****")
        for nick, theplayer in list(self.fighters.iteritems()):
            self.on_forfeit(nick)
            self.app.tell(nick,
            "**** BATTLE HAS BEEN ABORTED ****")
                 
    def on_battle_finish(_self, self, winid):
        pass

    def on_battle_command(_self, self, battlecommand):
        battlecommand.player.current_move = battlecommand
        do_time = self.gametime + battlecommand.tick_delay
        self.actions.append( (do_time, battlecommand) )
        
    def on_battle_execute(_self, self, bcomm):
        targetp = self.fighters[bcomm.target]
        bcomm.player.superpoints -= bcomm.super * 100
        if bcomm.move.element == "physical":
            power = bcomm.move.power + bcomm.super * 50
            st = bcomm.player.character.pstrength
            df = targetp.character.pdefense
            maxhp = self.settings.starthealth      
            damage = calculate_damage(st, df, power, maxhp)
            if is_critical(st, df):
                critdamage = calculate_damage(st,df,power * CRITICAL_POWER_FACTOR, maxhp) - damage
            else:
                critdamage = 0
            if targetp.current_move and targetp.current_move.name == 'Block':
                if random.randint(0, 2) == 0:
                    damage = 0
                    self.app.signals['game_msg'].emit(self.parse_message(
                        bcomm.target, bcomm.player.character.block_success_msg, bcomm.player.nickname))
                    bcomm.player.current_move = None
                    return
                else:
                    damage = int(damage * (2 / 3.0))
                    self.app.signals['game_msg'].emit(self.parse_message(
                        bcomm.target, bcomm.player.character.block_fail_msg, bcomm.player.nickname))

            self.app.signals['battle_damage'].emit(
                bcomm.player.nickname, bcomm.target, damage, critdamage) # int(self.move.power / 10))
        else:
            bcomm.player.magicpoints -= bcomm.mpcost
            if bcomm.move.element == "heal":
                power = bcomm.move.power
                st = bcomm.player.character.pstrength
                maxhp = self.settings.maxhealth
                healing = (maxhp / (200 - power)) * (math.log(st) / 80 + 10) + random.randrange(-maxhp * 0.01, maxhp * 0.01)
                self.app.signals['battle_damage'].emit(bcomm.player.nickname, bcomm.target, -healing)
        
    def on_battle_damage(_self, self, nickname, targetname, damage, critdmg=0):
        totaldmg = damage + critdmg
        theplayer = self.fighters[nickname]
        theplayer.superpoints += int(totaldmg / 20.0)
        theplayer.superpoints = min(self.app.game.settings.maxsuper, theplayer.superpoints)
        thetarget = self.fighters[targetname]
        thetarget.health -= totaldmg
        thetarget.health = min(self.app.game.settings.maxhealth, thetarget.health)
        thetarget.superpoints += int(totaldmg / 10.0)
        thetarget.superpoints = min(self.app.game.settings.maxsuper, thetarget.superpoints)
        if theplayer.current_move.super:
            hit_msg = self.app.game.parse_message(nickname, theplayer.current_move.move.supr_hit_msg, targetname)
        else:
            if critdmg:
                hit_msg = self.app.game.parse_message(nickname, theplayer.current_move.move.crit_hit_msg, targetname)
            else:
                hit_msg = self.app.game.parse_message(nickname, theplayer.current_move.move.hit_msg, targetname)
        if critdmg:
            hit_msg = "%s [%d+%d crit]" % (hit_msg, abs(damage), critdmg)
        else:
            hit_msg = "%s [%d]" % (hit_msg, abs(damage))
            
        self.app.signals['game_msg'].emit(hit_msg)
        if thetarget.health <= 0:
            death_msg = self.parse_message(targetname, thetarget.character.death_msg, nickname)
            self.app.signals['game_msg'].emit(death_msg)
            self.app.signals['game_msg'].emit(
            "Death slaps a sticker on %s, \"Kaput!\", you're dead. [%d]" % (
            thetarget.nickname, thetarget.health))
        theplayer.current_move = None
        winid = _self.check_win_condition(self)
        if winid != None:
            self.app.signals['battle_finish'].emit(winid)
        elif self.is_ready(nickname):
            self.app.signals['game_msg'].emit(theplayer.status_msg)
        
        
    def on_defect(_self, self):
        pass
        
    def is_ready(_self, self, nickname):
        theplayer = self.fighters[nickname]
        if not theplayer.current_move:
            return True
            
    def validate_target(_self, self, nickname, targetname, move):
        ttype = move.target
        target = None
        
        if not targetname and ttype in ['ally', 'enemy']:
            raise ValidationError( 
            "The '%s' move requires a target. (%s)" % (move.fullname, ttype))
        elif not targetname and ttype in ['self', 'ally-all', 'enemy-all']:
            return True
        elif targetname and ttype in ['ally', 'enemy']:
            target, left = validation.fighter(self.app, nickname, [targetname])    

            if ttype == "ally":
                if self.is_enemy(nickname, targetname):
                    raise ValidationError(
                    "'%s' can only target allies." % (move.fullname))
                elif self.fighters[targetname].health <= 0:
                    raise ValidationError(
                    "%s is dead man. They're dead." % targetname)
                else:
                    return True
            elif ttype == "enemy":
                if not self.is_enemy(nickname, targetname):
                    raise ValidationError(
                    "%s' can only target enemies." % (move.fullname))
                elif self.fighters[targetname].health <= 0:
                    raise ValidationError(
                    "%s is already dead. What good would that do?" % targetname)
                else:
                    return True
                                                                              
def refresh( gametype_name ):
    return imports.refresh(gametype_name)

def get( gametype_name ):
    return imports.get('gametypes', gametype_name)
