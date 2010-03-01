import random

from twisted.internet.task import LoopingCall

from urb.db import *
from urb.constants import *
from urb import imports, commands, validation, contexts
from urb.validation import ValidationError
from urb.player import Player, Session
from urb.util import dlog, dtrace

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
    
    def check_win_condition(self):
        pass
            
    def _get_paused(self):
        return not self.tick_timer.running
    paused = property(_get_paused)
        
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
            "The '%s' move requires a target. (%s)" % (move.fullname, ttype))
        elif not target and ttype in ['self', 'ally-all', 'enemy-all']:
            return True
        elif target and ttype in ['ally', 'enemy']:
            thetarget, left = validation.fighter(self.app, target.nickname, [target.nickname])    

            if ttype == "ally":
                if player.is_enemy(thetarget):
                    raise ValidationError(
                    "'%s' can only target allies." % (move.fullname))
                elif thetarget.health <= 0:
                    raise ValidationError(
                    "%s is dead man. They're dead." % targetname)
                else:
                    return True
            elif ttype == "enemy":
                if not player.is_enemy(thetarget):
                    raise ValidationError(
                    "%s' can only target enemies." % (move.fullname))
                elif thetarget.health <= 0:
                    raise ValidationError(
                    "%s is already dead. What good would that do?" % targetname)
                else:
                    return True
            
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
                
    def parse_message(self, player, message, target=None):
        if "%NIK" in message:
            message = message.replace("%NIK", player.nickname)
        if "%CHR" in message and player.character:
            message = message.replace("%CHR",  player.character.fullname)
        if "%TGT" in message and target:
            message = message.replace("%TGT", target.nickname)
        return message
        
    def open_selection(self):
        if self.state == "idle":
            self.fighters = {}
            self.state = "selection"
            self.app.signals['global_msg'].emit(
            "# Character Selection is now open for: %s." % self.name.capitalize())
        elif self.state == "prebattle":
            self.state = "selection"
            self.app.signals['global_msg'].emit(
            "# ! Battle delayed ---------------")
            self.app.signals['global_msg'].emit(
            "# Character Selection is now open for: %s." % self.name.capitalize())

    def close_selection(self):
        if self.state == "selection":
            for nick, player in self.fighters.iteritems():
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
                    player.tell("!! Battle is waiting on you to, 'ready' !!")
     
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
                join_msg = self.parse_message(player, char.selection_msg)
                self.app.signals['game_msg'].emit(join_msg)  
                
    def player_toggle_ready(self, player):
        if player.character:
            if player.ready:
                player.current_move = "unready"
                self.app.signals['game_msg'].emit("# ! - %s is no longer ready!" % player.nickname)
                player.tell("You are no longer ready for battle.")
            else:
                player.current_move = None
                player.tell("You are now ready for battle.")
                if len(self.get_ready()) == len(self.fighters):
                    self.app.signals['game_msg'].emit("## All players are READY! ##")
        else:
            player.tell("You cannot 'ready' until you 'pick' a character.")
            player.tell("Use 'chars' to get a list of available characters.")
            
    def prep_player(self, player):
       if player in self.fighters:
           player.character = None
           player.current_move = "unready"
           player.health = self.settings.starthealth
           player.magicpoints = self.settings.startmagic
           player.superpoints = self.settings.startsuper
           player.team = self.next_team_id
           self.next_team_id += 1
           
           player.session.switch('prebattle') 
            
    def process_battle_input(self, player, command, args):
        thechar = player.character
        # Process super syntax
        super = 0
        if '*' in command:
            try:
                command, super = command.split('*')
                super = int(super)
            except:
                player.tell("Your command couldn't be parsed. If supering, your move should look like 'fireball*3'.")
        themove = Move.get(selector=command)
        if themove in thechar.moves:
            # Check if battle is paused               
            if self.is_paused():
                player.tell("The battle is paused, you'll have to wait to '%s'." % command)
                return True
            # Check if player is alive
            elif player.health <= 0:
                player.tell("You can't do '%s' when you're DEAD!" % themove.fullname)
                return True
            # Check if player is ready
            elif not player.ready:
                if player.current_move.target:
                    player.tell("You can't do '%s' while you're doing '%s' on %s." % (
                    command, player.current_move.name,
                    player.current_move.target))
                else:
                    player.tell("You can't do '%s' while you're doing '%s'." % (
                    command, player.current_move.name))
                return True
            # Player is ready
            elif player.ready:
                # Establish target or find one
                targetname = args[0] if len(args) >= 1 else None
                if not targetname:
                    targetname = self.find_target(player, themove.target).nickname
                    if not targetname:
                        player.tell("You couldn't find a valid target!")
                        return True
               # Validate the target against move-type
                try:
                    target = self.fighters[targetname]
                    self.validate_target(player, target, themove)
                except validation.ValidationError, e:
                    player.tell(e.message)
                    return True
                else:
                    # Validate super usage
                    if super > 0:
                        if not themove.cansuper:
                            player.tell("The '%s' move can't be supered." % (themove.fullname))
                            return True
                        if player.superpoints < super * 100:
                            player.tell("You don't have enough Super to do a level %d '%s'!" % (super, themove.fullname))
                            return True
                        if super > self.settings.maxsuperlevel:
                            player.tell("The max super-level is currently: %d" % self.settings.maxsuperlevel)
                            return True
                    # Validate magic usage
                    mpcost = 0
                    if themove.element != 'physical':
                        mpcost = math.ldexp(move.power, 1) / math.log(6000) * 10
                        if player.magicpoints < mpcost:
                            player.tell("You don't have enough Magic to do '%s'!" % move.fullname)
                            return True
                    # Queue the battle command
                    bcommand = contexts.battle.BattleCommand(self.app, player, themove, target, mpcost, super)
                    player.current_move = bcommand
                    do_time = self.gametime + bcommand.tick_delay
                    self.actions.append( (do_time, bcommand) )
                    return True
        
    def start_battle(self):
        if self.state == "prebattle":
            unready = self.get_unready()
            for player in unready:
                self.app.signals['game_msg'].emit(
                "%s was dropped from the battle." % player)
                self.player_forfeit(player)
                player.tell("You were dropped from battle for not being ready.")
            for nickname, player in self.fighters.iteritems():
                player.session.switch('battle')
            self.app.signals['game_msg'].emit(
            "****  BATTLE HAS BEGUN ****")
            self.tick_timer.start(self.tickrate)
        
    def pause_battle(self):
        pass
        
    def resume_battle(self):
        pass
        
    def abort_battle(self):
        if self.tick_timer.running:
            self.tick_timer.stop()
        self.actions = []
        self.app.signals['game_msg'].emit(
        "**** BATTLE HAS BEEN ABORTED ****")
        for nick, player in list(self.fighters.iteritems()):
            self.player_forfeit(player)
            player.tell("**** BATTLE HAS BEEN ABORTED ****")
        
    def finish_battle(self, winid):
        team = self.get_team(winid)
        winner = team[0]
        self.app.signals['game_msg'].emit(
        "****  ! BATTLE IS OVER !  ****")
        self.state = "idle"
        self.tick_timer.stop()
        for nick, theplayer in list(self.fighters.iteritems()):
            self.player_forfeit(theplayer)
        self.actions = []
        
    def battle_damage(self, player, target, damage, crit=0):
        totaldmg = damage + crit
        
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
        player.superpoints = min(self.settings.maxsuper, player.superpoints)
        # Apply Damage
        target.health -= totaldmg
        target.health = min(self.settings.maxhealth, target.health)
        # Target Earn Super-Points
        target.superpoints += int(totaldmg / 10.0)
        target.superpoints = min(self.settings.maxsuper, target.superpoints)
        
        # Emit Hit/Critical Messages        
        if player.current_move.super:
            hit_msg = self.parse_message(player, player.current_move.move.supr_hit_msg, target)
        else:
            if crit:
                hit_msg = self.parse_message(player, player.current_move.move.crit_hit_msg, target)
            else:
                hit_msg = self.parse_message(player, player.current_move.move.hit_msg, target)
        if crit:
            hit_msg = "%s [%d+%d crit]" % (hit_msg, abs(damage), crit)
        elif damage:
            hit_msg = "%s [%d]" % (hit_msg, abs(damage))     
        self.app.signals['game_msg'].emit(hit_msg)
        # Element Specific Descriptions
        if player.current_move.move.element == "demi":
            self.app.signals['game_msg'].emit("%s just lost half their health!" % target.nickname)   
        elif player.current_move.move.element == "hpdrain":
            self.app.signals['game_msg'].emit("%s grows stronger from %s's stolen lifeforce!" % (player, target))
        
    def battle_do(self, bcomm):
        #======================================================================
         # delegate_dict = {
         #                'physical':    self.on_battle_physical,
         #                #'heal':        self.on_battle_heal,
         # }
         # if bcomm.move.element in delegate_dict:
         #   handler = delegate_dict[bcomm.move.element]
         #   args = (
         #           bcomm.player,
         #           bcomm.target,
         #           bcomm.move,
         #           )
         #   handler()
         #======================================================================
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

            self.battle_damage(bcomm.player, bcomm.target, damage, critdamage) # int(self.move.power / 10))
        else:
            bcomm.player.magicpoints -= bcomm.mpcost
            power = bcomm.move.power
            maxhp = self.settings.maxhealth
            strength = bcomm.player.character.mstrength
            defense = bcomm.target.character.mdefense
            if bcomm.move.element == "heal":
                healing = calculate_damage(strength, 25, power, maxhp) + int(random.randrange(-maxhp * 0.03, maxhp * 0.03))
                self.battle_damage(bcomm.player, bcomm.target, -healing)
            elif bcomm.move.element == "demi":
                targethp = bcomm.target.health
                ratio = targethp / float(maxhp)
                ratio = min(MAX_DEMI_RATIO, ratio)
                if random.random() > ratio:
                    damage = int(targethp / 2.0)
                    self.battle_damage(bcomm.player, bcomm.target, damage)
                else:
                    self.app.signals['game_msg'].emit(self.parse_message(
                        bcomm.player, bcomm.move.miss_msg, bcomm.target))
            elif bcomm.move.element == "hpdrain":
                damage = calculate_damage(strength, defense, power, maxhp)+ int(random.randrange(-maxhp * 0.01, maxhp * 0.01))
                stolen = damage * (challenge_factor(strength, defense) - 1)
                bcomm.player.health += stolen
                bcomm.player.health = min(self.settings.maxhealth, bcomm.player.health)
                self.battle_damage(bcomm.player, bcomm.target, damage)
    
    def tick(self):
        for fighter in self.fighters.values():
            fighter.magicpoints = min(self.settings.maxmagic, fighter.magicpoints + self.settings.mprate)
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
                if not action[1].alive:
                    self.actions.remove(action)
                        
    def start_battle_timers(self):
        self.tick_timer.start(self.tickrate)
    
    def stop_battle_timers(self):
        self.tick_timer.stop()
