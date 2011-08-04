import random

from twisted.internet.task import LoopingCall

from urb.db import *
from urb.constants import *
from urb import imports, commands, validation, contexts, effects
from urb.validation import ValidationError
from urb.player import Player, Session
from urb.util import dlog, dtrace, render, word_table

def refresh( gametype_name ):
    return imports.refresh(gametype_name)

def get( gametype_name ):
    return imports.get('gametypes', gametype_name)

class GameEngine(object):
    name = 'survivor'

    def __init__(self, app):
        self.app = app

        self.fighters = {}
        self.next_team_id = 0
        
        self.gametime = 0
        self.tickrate = 1.0
        self.tick_timer = LoopingCall(self.tick)
        self.actions = []
        
        self.state = "idle" # idle, selection prebattle battle
        
    def _get_players(self):
        return self.app.players
    players = property(_get_players)
        
    def _get_settings(self):
        gs = GameSettings.get(selector=self.name)
        if gs == None:
            gs = GameSettings.create(self.name)
        return gs 
    settings = property(_get_settings)
            
    def _get_paused(self):
        return not self.tick_timer.running
    paused = property(_get_paused)
            
    def get_ready(self):
        ready = []
        for nick, theplayer in self.fighters.iteritems():
            if theplayer.ready == True:
                ready.append(theplayer)
        return ready
        
    def get_unready(self):
        unready = []
        for nick, theplayer in self.fighters.iteritems():
            if theplayer.ready == False:
                unready.append(theplayer)
        return unready
        
    def get_team(self, id):
        theteam = []
        for nick, theplayer in self.fighters.iteritems():
            if theplayer.team == id:
                theteam.append(theplayer)
        return theteam
        
    def get_allies(self, player):
        theteam = self.get_team(player.team)
        theteam.remove(player)
        return theteam
        
    def get_enemies(self, player):
        enemies = []
        for nick, otherplayer in self.fighters.iteritems():
            if otherplayer.team != player.team:
                enemies.append(otherplayer)
        return enemies
                
    def check_win_condition(self):
        pass
    
    def find_target(self, player, ttype):
        if ttype == 'ally':
            allies = self.get_allies(player)
            return random.choice(allies)
        elif ttype == 'enemy':
            enemies = self.get_enemies(player)
            if len(enemies):
                return random.choice(enemies)
            else:
                return None
        elif ttype == 'self':
            return player
            
    def validate_target(self, player, target, move):
        ttype = move.target
        thetarget = None
        
        if not target and ttype in ['ally', 'enemy']:
            raise ValidationError( 
            "* The '%s' move requires a target. (%s)" % (move.fullname, ttype))
        elif not target and ttype in ['self', 'ally-all', 'enemy-all']:
            return True
        elif target and ttype in ['ally', 'enemy']:
            thetarget, left = validation.fighter(self.app, target.nickname, [target.nickname])    
            if ttype == "ally":
                if player.is_enemy(thetarget):
                    raise ValidationError(
                    "* '%s' can only target allies." % (move.fullname))
                elif thetarget.health <= 0:
                    raise ValidationError(
                    "* %s is dead man. They're dead." % target.nickname)
                else:
                    return True
            elif ttype == "enemy":
                if not player.is_enemy(thetarget):
                    raise ValidationError(
                    "* %s' can only target enemies." % (move.fullname), None)
                elif thetarget.health <= 0:
                    raise ValidationError(
                    "* %s is already dead. What good would that do?" % target.nickname)
                else:
                    return True
        
    def open_selection(self):
        if self.state == "idle":
            self.fighters = {}
            self.state = "selection"
            self.app.gsay(" * Character Selection is now OPEN for: %s * " % self.name.capitalize(), fmt="-^")
            self.app.gsay(" use 'fight' to join up! ", fmt="-^", channel=False)
        elif self.state == "prebattle":
            self.state = "selection"
            self.app.fsay(" * Battle delayed * ", fmt="-^")
            self.app.gsay(" Character Selection is now OPEN for: %s " % self.name.capitalize(), fmt="-^")
            self.app.gsay(" use 'fight' to join up! ", fmt="-^", channel=False)

    def close_selection(self):
        if not self.fighters:
            self.app.game = None
            self.app.gsay(" * Character Selection is now CLOSED. * ", fmt="-^")
            return
        if self.state == "selection":
            parts = []
            lines = []
            for nick, player in self.fighters.iteritems():
                char = player.character.fullname if player.character else "NO CHAR"
                parts.append("%s(%s)" % (nick, char))
                parts.append("  -  %d HP : %d MP : %d SP %s" % (player.health, player.magicpoints, player.superpoints, ": READY" if player.ready else ""))
                lines = word_table(parts, 2, fmt=" <")
            for line in lines:
                self.app.gsay(line)
            if len(self.get_ready()) == len(self.fighters):
                self.app.gsay(" * Character Selection is now closed. * ", fmt="-^")
                self.state = "prebattle"
            else:
                self.app.fsay(" * Waiting for all players to READY. * ", fmt="-^")
                unready = self.get_unready()
                print "UNREADY", [(p.nickname, p.ready) for p in unready]
                for theplayer in unready:
                    theplayer.tell("(!) Battle is waiting on you to, 'ready' !!")
     
    def player_signup(self, player, character):
        print "---------------------"
        if player in self.players:
            self.fighters[player.nickname] = player
            self.prep_player(player)
            if character:
                self.player_pick(player, character.selector)
            
    def player_forfeit(self, player):
        if player in self.fighters:
            player.session.switch('mainmenu')
            del self.fighters[player.nickname]
        
    def player_pick(self, player, selector):
        if player in self.fighters:
            char = Character.get(selector=selector)
            if char:
                player.character = char
                join_msg = render(char.selection_msg, player)
                self.app.fsay(join_msg)  
                
    def player_toggle_ready(self, player):
        if player.character:
            if player.ready:
                player.current_move = "unready"
                self.app.fsay(" %s is no longer ready " % player.nickname, fmt="!^")
                player.tell("* You are no longer ready for battle.")
            else:
                player.current_move = None
                player.tell("* You are now ready for battle.")
                if len(self.get_ready()) == len(self.fighters):
                    self.app.fsay(" * All players are READY * ", fmt="-^")
        else:
            player.tell("* You cannot 'ready' until you 'pick' a character.")
            player.tell("* Use 'chars' to get a list of available characters.")
            
    def prep_player(self, player):
       if player in self.fighters:
           player.character = None
           player.current_move = "unready"
           player.health = self.settings.starthealth
           player.magicpoints = self.settings.startmagic
           player.superpoints = self.settings.startsuper
           player.team = self.next_team_id
           player.effects = {}
           self.next_team_id += 1
           
           player.session.switch('prebattle') 
           
    def tick(self):
        for fighter in self.fighters.values():
            fighter.magicpoints = min(self.settings.maxmagic, fighter.magicpoints + self.settings.mprate)
            for effect in fighter.effects.values():
                effect.tick()
        winid = self.check_win_condition()
        if winid != None:
            self.app.game.finish_battle(winid)
        self.gametime += 1
        if self.actions:
            for action in list(self.actions):
                if action[0] <= self.gametime:
                    if action[1].alive:
                        action[1].alive = False
                        action[1].perform()
                if not action[1].alive and action in self.actions:
                    self.actions.remove(action)
                        
    def start_battle_timers(self):
        self.tick_timer.start(self.tickrate)
    
    def stop_battle_timers(self):
        self.tick_timer.stop()
           
    def start_battle(self):
        if self.state == "prebattle":
            unready = self.get_unready()
            for player in unready:
                self.app.fsay("* %s was dropped from the battle." % player)
                self.player_forfeit(player)
                player.tell("* You were dropped from battle for not being ready.")
            for nickname, player in self.fighters.iteritems():
                player.session.switch('battle')
            self.app.fsay("# BATTLE HAS BEGUN #", fmt="*^")
            self.tick_timer.start(self.tickrate)
        
    def pause_battle(self):
        pass
        
    def resume_battle(self):
        pass
        
    def get_paused(self):
        return False
    def set_paused(self, val):
        pass
    paused = property(get_paused, set_paused)

    def abort_battle(self):
        if self.tick_timer.running:
            self.tick_timer.stop()
        self.actions = []
        self.app.fsay(" ! BATTLE HAS BEEN ABORTED ! ", fmt="*^")
        for nick, player in list(self.fighters.iteritems()):
            self.player_forfeit(player)
            player.tell(" ! BATTLE HAS BEEN ABORTED ! ", fmt="*^")
        
    def finish_battle(self, winid):
        team = self.get_team(winid)
        winner = team[0]
        self.app.fsay(" ! BATTLE IS OVER ! ", fmt="*^")
        self.state = "idle"
        self.tick_timer.stop()
        for nick, theplayer in list(self.fighters.iteritems()):
            self.player_forfeit(theplayer)
        self.actions = []
            

    ##
    ##  check_ methods return True if the check has Failed
    ##  not whether the item the method name describes is True
    ##

    def check_paused(self, player, move, target=None):
        if self.paused:
            player.tell("* The battle is paused, you'll have to wait to '%s'." % command)
            return True

    def check_player_alive(self, player, move):
        if player.health <= 0:
            player.tell("* You can't do '%s' when you're DEAD!" % themove.fullname)
            return True    

    def check_player_ready(self, player, move):
        if not player.ready:
            if player.current_move.target:
                player.tell("* You can't do '%s' while you're doing '%s' on %s." % (
                move.selector, player.current_move.name,
                player.current_move.target))
            else:
                player.tell("* You can't do '%s' while you're doing '%s'." % (
                move.selector, player.current_move.name))
            return True

    def check_super_usage(self, player, move, super):
        if super > 0:
            if not move.cansuper:
                player.tell("* The '%s' move can't be supered." % (move.fullname))
                return True
            if player.superpoints < super * 100:
                player.tell("* You don't have enough Super to do a level %d '%s'!" % (super, move.fullname))
                return True
            if super > self.settings.maxsuperlevel:
                player.tell("* The max super-level is currently: %d" % self.settings.maxsuperlevel)
                return True

    def check_magic_usage(self, player, move, target):
        mpcost = move.mpcost
        if move.element != 'physical' and player.magicpoints < mpcost:
           player.tell("* You don't have enough Magic to do '%s'!" % move.fullname)
           return True

    def calculate_delay(self, player, move, target):
        return int(move.power / 10)        

    def output_preperation(self, player, move, super, target):
        if super:
            prepare_msg = render(move.supr_prepare_msg, player, target)
            prepare_msg = ("L%d SUPER ~ " % super) + prepare_msg
        else:
            prepare_msg = render(move.prepare_msg, player, target)
        self.app.fsay(prepare_msg)


    def get_battle_command(self, player, move, super, delay, target):
        """ Return the battle command or None. If None make sure to tell the player why """
        return contexts.battle.BattleCommand(self.app, player, move, target, delay, super)

    def process_battle_input(self, player, command, args):
        """
        Process input during battle, doing validation to ensure that when
        the command executes, it was legal.

        return True if we handled the input

        """
        thechar = player.character
        # Process super syntax
        super = 0
        if '*' in command:
            try:
                command, super = command.split('*')
                super = int(super)
            except:
                player.tell("* Your command couldn't be parsed. If supering, your move should look like 'fireball*3'.")
                return True
        themove = Move.get(selector=command)
        
        # check for move-prevention : stun
        if themove in thechar.moves:
            if 'stun' in player.effects:
                player.tell(player.effects['stun'].get_denial(themove))
                return True
            # Check if battle is paused               
            if self.check_paused(player, themove):
                return True
            # Check if player is alive
            if self.check_player_alive(player, themove):
                return True
            # Check if player is ready
            if self.check_player_ready(player, themove):
                return True
            # Establish target or find one
            targetname = args[0] if len(args) >= 1 else None
            if not targetname:
                targetname = self.find_target(player, themove.target).nickname
                if not targetname:
                    player.tell("* You couldn't find a valid target!")
                    return True
            # Validate the target against move-type
            target = self.fighters[targetname]
            try:
                self.validate_target(player, target, themove)
            except validation.ValidationError, e:
                player.tell(e.message)
                return True
            else:
                # Validate super usage
                if self.check_super_usage(player, themove, super):
                    return True
                # Validate magic usage
                if self.check_magic_usage(player, themove, target):
                    return True
                # Calculate Delay
                delay = self.calculate_delay(player, themove, target)
                # Output action strings
                self.output_preperation(player, themove, super, target)
                # Queue the battle command
                print "TARGET", target
                bcommand = self.get_battle_command(player, themove, super, delay, target)
                if bcommand:
                    player.current_move = bcommand
                    do_time = self.gametime + bcommand.tick_delay
                    self.actions.append( (do_time, bcommand) )
                return True
        
    def battle_do(self, bcomm):
        player = bcomm.player
        target = bcomm.target
        move = bcomm.move

        player.superpoints -= bcomm.super * 100
        # Physical Moves
        if move.element == "physical":
            # increase move power based on super
            power = 0 if 'blind' in player.effects else move.power + bcomm.super * 50
            st = player.character.pstrength
            df = target.character.pdefense
            maxhp = self.settings.maxhealth      
            damage = int(calculate_damage(st, df, power, maxhp) + int(random.randrange(-maxhp * 0.05, maxhp * 0.05)))
            if is_critical(st, df):
                critdamage = calculate_damage(st,df,power * CRITICAL_POWER_FACTOR, maxhp) - damage
            else:
                critdamage = 0
            if target.current_move and target.current_move.name == 'Block':
                if random.randint(0, 2) == 0:
                    damage = 0
                    self.app.fsay(render(player.character.block_success_msg, target, player))
                    player.current_move = None
                    return
                else:
                    damage = int(damage * (2 / 3.0))
                    self.app.fsay(render(player.character.block_fail_msg, target, player))

            self.battle_damage(player, target, damage, critdamage) # int(self.move.power / 10))
            effects.get('stun')(self.app, player, move, target)
            print "EFFECTS ON TARGET", target.effects
        # Magical Moves
        else:
            player.magicpoints -= bcomm.mpcost
            power = move.power
            maxhp = self.settings.maxhealth
            strength = player.character.mstrength
            defense = target.character.mdefense
            if move.element == "heal":
                healing = int(calculate_damage(strength, 25, power, maxhp) + int(random.randrange(-maxhp * 0.03, maxhp * 0.03)))
                self.battle_damage(player, target, -healing)
            elif move.element == "demi":
                targethp = target.health
                ratio = targethp / float(maxhp)
                ratio = min(MAX_DEMI_RATIO, ratio)
                if random.random() > ratio:
                    damage = int(targethp / 2.0)
                    self.battle_damage(player, target, damage)
                else:
                    self.app.fsay(render(move.miss_msg, player, target))
            elif move.element == "hpdrain":
                damage = calculate_damage(strength, defense, power, maxhp)+ int(random.randrange(-maxhp * 0.01, maxhp * 0.01))
                stolen = damage * (challenge_factor(strength, defense) - 1)
                player.health += stolen
                player.health = min(self.settings.maxhealth, player.health)
                self.battle_damage(player, target, damage)
            
        if target.health <= 0:
            death_msg = render(target.character.death_msg, target, player)
            self.app.fsay(death_msg)
            self.app.fsay("Death slaps a sticker on %s, \"Kaput!\", you're dead. [%d]" % (target, target.health))
        winid = self.app.game.check_win_condition()
        if winid != None:
            self.finish_battle(winid)            
        else:
            player.current_move = None
            self.app.fsay(player.status_msg)
                
    def battle_damage(self, player, target, damage, crit=0):
        totaldmg = damage + crit
        
        # Weakness / Resistance Modifications
        if player.current_move.move.element not in ['demi', 'heal']:
            element = player.current_move.move.element
            if element == target.character.weakness:
                totaldmg = int(totaldmg * random.randrange(150, 300) / 100.0)
                self.app.fsay("%s's '%s' is super effective against %s!" %
                    player, player.current_move.move.fullname, target)
            elif element == target.character.resistance:
                totaldmg = int(totaldmg * random.randrange(150, 300) / 100.0)
                self.app.fsay("%s's '%s' isn't effective against %s!" %
                    player, player.current_move.move.fullname, target)
        # Attacker Earn Super-Points        
        player.superpoints += int(abs(totaldmg) / 20.0)
        player.superpoints = min(self.settings.maxsuper, player.superpoints)
        # Apply Damage
        target.health -= int(totaldmg)
        target.health = min(self.settings.maxhealth, target.health)
        # Target Earn Super-Points
        target.superpoints += int(abs(totaldmg) / 10.0)
        target.superpoints = min(self.settings.maxsuper, target.superpoints)
        
        # Emit Hit/Critical Messages        
        if player.current_move.super:
            hit_msg = render(player.current_move.move.supr_hit_msg, player, target)
        else:
            if crit:
                hit_msg = render(player.current_move.move.crit_hit_msg, player, target)
            else:
                hit_msg = render(player.current_move.move.hit_msg, player, target)
        if crit:
            hit_msg = "%s [%d+%d crit]" % (hit_msg, abs(damage), crit)
        elif damage:
            hit_msg = "%s [%d]" % (hit_msg, abs(damage))     
        self.app.fsay(hit_msg)
        # Element Specific Descriptions
        if player.current_move.move.element == "demi":
            self.app.fsay("%s just lost half their health!" % target.nickname)   
        elif player.current_move.move.element == "hpdrain":
            self.app.fsay("%s grows stronger from %s's stolen lifeforce!" % (player, target))
