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
    
    def on_prep_player(_self, self, player):
        if player in self.fighters:
            player.character = None
            player.current_move = "unready"
            player.health = self.settings.starthealth
            player.magicpoints = self.settings.startmagic
            player.superpoints = self.settings.startsuper
            player.team = self.next_team_id
            self.next_team_id += 1
            
            player.session.switch('prebattle')    
            
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
                    self.app.tell(theplayer,
                        "!! Battle is waiting on you to, 'ready' !!")
            
                        
    def on_battle_start(_self, self):
        if self.state == "prebattle":
            unready = self.get_unready()
            for player in unready:
                self.app.signals['game_msg'].emit(
                "%s was dropped from the battle." % player)
                self.on_forfeit(player)
                self.app.tell(player,
                "You were dropped from battle for not being ready.")
            for nickname, player in self.fighters.iteritems():
                player.session.switch('battle')
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
        for nick, player in list(self.fighters.iteritems()):
            self.on_forfeit(player)
            self.app.tell(player,
            "**** BATTLE HAS BEEN ABORTED ****")
                 
    def on_battle_finish(_self, self, winid):
        pass

    def on_battle_queue(_self, self, battlecommand):
        battlecommand.player.current_move = battlecommand
        do_time = self.gametime + battlecommand.tick_delay
        self.actions.append( (do_time, battlecommand) )
        
    def on_battle_do(_self, self, bcomm):
        #=======================================================================
        # delegate_dict = {
        #                 'physical':    self.on_battle_physical,
        #                 #'heal':        self.on_battle_heal,
        # }
        # if bcomm.move.element in delegate_dict:
        #    handler = delegate_dict[bcomm.move.element]
        #    args = (
        #            bcomm.player,
        #            bcomm.target,
        #            bcomm.move,
        #            )
        #    handler()
        #=======================================================================
        targetp = self.fighters[bcomm.target]
        bcomm.player.superpoints -= bcomm.super * 100
        if bcomm.move.element == "physical":
            power = bcomm.move.power + bcomm.super * 50
            st = bcomm.player.character.pstrength
            df = targetp.character.pdefense
            maxhp = self.settings.starthealth      
            damage = calculate_damage(st, df, power, maxhp) + int(random.randrange(-maxhp * 0.05, maxhp * 0.05))
            if is_critical(st, df):
                critdamage = calculate_damage(st,df,power * CRITICAL_POWER_FACTOR, maxhp) - damage
            else:
                critdamage = 0
            if targetp.current_move and targetp.current_move.name == 'Block':
                if random.randint(0, 2) == 0:
                    damage = 0
                    self.app.signals['game_msg'].emit(self.parse_message(
                        bcomm.target, bcomm.player.character.block_success_msg, bcomm.player))
                    bcomm.player.current_move = None
                    return
                else:
                    damage = int(damage * (2 / 3.0))
                    self.app.signals['game_msg'].emit(self.parse_message(
                        bcomm.target, bcomm.player.character.block_fail_msg, bcomm.player))

            self.app.signals['battle_damage'].emit(
                bcomm.player, bcomm.target, damage, critdamage) # int(self.move.power / 10))
        else:
            bcomm.player.magicpoints -= bcomm.mpcost
            power = bcomm.move.power
            maxhp = self.settings.maxhealth
            strength = bcomm.player.character.mstrength
            defense = bcomm.target.character.mdefense
            if bcomm.move.element == "heal":
                healing = calculate_damage(strength, 25, power, maxhp) + int(random.randrange(-maxhp * 0.03, maxhp * 0.03))
                self.app.signals['battle_damage'].emit(bcomm.player, bcomm.target, -healing)
            elif bcomm.move.element == "demi":
                targethp = bcomm.target.health
                ratio = targethp / float(maxhp)
                ratio = min(MAX_DEMI_RATIO, ratio)
                if random.random() > ratio:
                    damage = int(targethp / 2.0)
                    self.app.signals['battle_damage'].emit(bcomm.player, bcomm.target, damage)
                else:
                    self.app.signals['game_msg'].emit(self.parse_message(
                        bcomm.player, bcomm.move.miss_msg, bcomm.target))
            elif bcomm.move.element == "hpdrain":
                damage = calculate_damage(strength, defense, power, maxhp)+ int(random.randrange(-maxhp * 0.01, maxhp * 0.01))
                stolen = damage * (challenge_factor(strength, defense) - 1)
                bcomm.player.health += stolen
                bcomm.player.health = min(self.app.game.settings.maxhealth, bcomm.player.health)
                self.app.signals['battle_damage'].emit(bcomm.player, bcomm.target, damage)
                
        
    def on_battle_damage(_self, self, player, target, damage, critdmg=0):
        totaldmg = damage + critdmg
        
        # Weakness / Resistance Modifications
        if player.current_move.move.element not in ['demi', 'heal']:
            element = player.current_move.move.element
            if element == target.character.weakness:
                totaldmg = int(totaldmg * random.randrange(150, 300) / 100.0)
                self.app.signals['game_msg'].emit("%s's '%s' is super effective against %s!" %
                    player, player.current_move.move.fullname, target)
            elif element == target.character.resistance:
                totaldmg = int(totaldmg * random.randrange(150, 300) / 100.0)
                self.app.signals['game_msg'].emit("%s's '%s' isn't effective against %s!" %
                    player, player.current_move.move.fullname, target)
        # Attacker Earn Super-Points        
        player.superpoints += int(totaldmg / 20.0)
        player.superpoints = min(self.app.game.settings.maxsuper, player.superpoints)
        # Apply Damage
        target.health -= totaldmg
        target.health = min(self.app.game.settings.maxhealth, target.health)
        # Target Earn Super-Points
        target.superpoints += int(totaldmg / 10.0)
        target.superpoints = min(self.app.game.settings.maxsuper, target.superpoints)
        
        # Emit Hit/Critical Messages        
        if player.current_move.super:
            hit_msg = self.app.game.parse_message(player, player.current_move.move.supr_hit_msg, target)
        else:
            if critdmg:
                hit_msg = self.app.game.parse_message(player, player.current_move.move.crit_hit_msg, target)
            else:
                hit_msg = self.app.game.parse_message(player, player.current_move.move.hit_msg, target)
        if critdmg:
            hit_msg = "%s [%d+%d crit]" % (hit_msg, abs(damage), critdmg)
        elif damage:
            hit_msg = "%s [%d]" % (hit_msg, abs(damage))     
        self.app.signals['game_msg'].emit(hit_msg)
        # Element Specific Descriptions
        if player.current_move.move.element == "demi":
            self.app.signals['game_msg'].emit("%s just lost half their health!" % target.nickname)   
        elif player.current_move.move.element == "hpdrain":
            self.app.signals['game_msg'].emit("%s grows stronger from %s's stolen lifeforce!" % (player, target))    
        
    def on_defect(_self, self):
        pass
        
    def is_ready(_self, self, player):
        if not player.current_move:
            return True
            
    def validate_target(_self, self, player, target, move):
        ttype = move.target
        thetarget = None
        
        if not target and ttype in ['ally', 'enemy']:
            raise ValidationError( 
            "The '%s' move requires a target. (%s)" % (move.fullname, ttype))
        elif not target and ttype in ['self', 'ally-all', 'enemy-all']:
            return True
        elif target and ttype in ['ally', 'enemy']:
            thetarget, left = validation.fighter(self.app, target.nickname, [target.nickname])    

            if ttype == "ally":
                if self.is_enemy(player, thetarget):
                    raise ValidationError(
                    "'%s' can only target allies." % (move.fullname))
                elif thetarget.health <= 0:
                    raise ValidationError(
                    "%s is dead man. They're dead." % targetname)
                else:
                    return True
            elif ttype == "enemy":
                if not self.is_enemy(player, thetarget):
                    raise ValidationError(
                    "%s' can only target enemies." % (move.fullname))
                elif thetarget.health <= 0:
                    raise ValidationError(
                    "%s is already dead. What good would that do?" % targetname)
                else:
                    return True
                                                                              
def refresh( gametype_name ):
    return imports.refresh(gametype_name)

def get( gametype_name ):
    return imports.get('gametypes', gametype_name)
