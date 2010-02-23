import random
import math

from urb import contexts, commands, validation
from urb.colors import colorize
from urb.util import dlog, metadata

class BlockCommand(commands.Command):
    def __init__(self, app, player):
        self.app = app
        self.player = player
        self.target = None
        self.app.signals['game_msg'].emit(self.app.game.parse_message(
            self.player.nickname, player.character.block_begin_msg))
        
    def _get_name(self):
        return 'Block'
    name = property(_get_name)


class BattleCommand(commands.Command):
    def __init__(self, app, player, move, target, mpcost=0):
        self.app = app
        self.player = player
        self.move = move
        self.target = target
        self.mpcost = mpcost
        
        self.tick_delay = int(self.move.power / 10)
        prepare_msg = self.app.game.parse_message(self.player.nickname, self.move.prepare_msg, target=target)
        self.app.signals['game_msg'].emit(prepare_msg)
        
    def _get_name(self):
        return self.move.fullname
    name = property(_get_name)
        
    def perform(self):
        targetp = self.app.game.fighters[self.target]
        if self.move.element == "physical":
            power = self.move.power
            st = self.player.character.pstrength
            df = targetp.character.pdefense
            maxhp = self.app.game.settings.maxhealth
            damage = (maxhp / (150 - power)) * (math.log(st) / df + 10) + random.randrange(-maxhp * 0.01, maxhp * 0.01)
            if targetp.current_move and targetp.current_move.name == 'Block':
                if random.randint(0, 2) == 0:
                    damage = 0
                    self.app.signals['game_msg'].emit(self.app.game.parse_message(
                        self.target, self.player.character.block_success_msg, self.player.nickname))
                    self.player.current_move = None
                    return
                else:
                    damage = int(damage * (2 / 3.0))
                    self.app.signals['game_msg'].emit(self.app.game.parse_message(
                        self.target, self.player.character.block_fail_msg, self.player.nickname))

            self.app.signals['battle_damage'].emit(
                self.player.nickname, self.target, damage) # int(self.move.power / 10))
        else:
            self.player.magicpoints -= self.mpcost
            if self.move.element == "heal":
                power = self.move.power
                st = self.player.character.pstrength
                maxhp = self.app.game.settings.maxhealth
                healing = (maxhp / (200 - power)) * (math.log(st) / 80 + 10) + random.randrange(-maxhp * 0.01, maxhp * 0.01)
                self.app.signals['battle_damage'].emit(self.player.nickname, self.target, -healing)

class BattleContext(contexts.Context):
    """You're in battle!"""    
    
    def on_input(_self, self, command, args):
        theplayer = self.app.game.fighters[self.nickname]
        thechar = theplayer.character
        themoves = self.app.database.get_moves_for(thechar.selector)
        for move in themoves:
            if move.selector == command:
                if self.app.game.is_paused():
                    self.app.tell(self.nickname,
                    "The battle is paused, you'll have to wait to '%s'." % command)
                    return True
                elif theplayer.health <= 0:
                    self.app.tell(self.nickname,
                    "You can't do '%s' when you're DEAD!" % move.fullname)
                    return True
                elif not self.app.game.is_ready(self.nickname):
                    if theplayer.current_move.target:
                        self.app.tell(self.nickname,
                        "You can't do '%s' while you're doing '%s' on %s." % (
                        command, theplayer.current_move.name,
                        theplayer.current_move.target))
                    else:
                        self.app.tell(self.nickname,
                        "You can't do '%s' while you're doing '%s'." % (
                        command, theplayer.current_move.name))
                    return True
                elif self.app.game.is_ready(self.nickname):
                    target = None
                    if len(args) >= 1:
                        target = args[0]
                    else:
                        target = self.app.game.get_target(self.nickname, move.target).nickname
                        if not target:
                            self.app.tell(self.nickname,
                            "You couldn't find a valid target!")
                            return True
                    try:
                        self.app.game.validate_target(self.nickname, target, move)
                    except validation.ValidationError, e:
                        self.app.tell(self.nickname, e.message)
                        return True
                    else:
                        mpcost = 0
                        if move.element != 'physical':
                            mpcost = math.ldexp(move.power, 1) / math.log(6000) * 10
                            if theplayer.magicpoints < mpcost:
                                self.app.tell(self.nickname, "You don't have enough Magic to do '%s'!" % move.fullname)
                                return True
                        bcommand = BattleCommand(self.app, theplayer, move, target, mpcost)
                        theplayer.current_move = bcommand
                        do_time = self.app.game.gametime + bcommand.tick_delay
                        self.app.game.actions.append( (do_time, bcommand) )
                        return True
                    
    def com_exit(_self, self, args):
        """Cancel battle participation."""
        self.app.signals['forfeit'].emit(self.nickname)
                        

    def com_roster(_self, self, args):
        """Get the current battle roster."""
        self.app.tell(self.nickname,
        " - The current battle-roster -")
        for nick, player in self.app.game.fighters.iteritems():
            if player.character:
                self.app.tell(self.nickname,
                "%s(%s) - %d HP - Ready: %s" % (
                nick, player.character.fullname,  player.health, self.app.game.is_ready(self.nickname)))
            else:
                self.app.tell(self.nickname,
                "%s(NO CHAR) - %d HP - Ready: %s" % (
                nick, player.health, player.ready))
    
    @metadata(schema=(('fighter*', 'nickname'),))           
    def com_status(_self, self, args):
        """Get the status for a player or yourself."""
        if 'nickname' in args:
            self.app.tell(self.nickname, args['nickname'].status_msg)
        else:
            self.app.tell(self.nickname, self.app.game.fighters[self.nickname].status_msg)
            
    def com_block(_self, self, args):
        """Block any incomming attacks."""
        if self.app.game.is_ready(self.nickname):
            theplayer = self.app.game.fighters[self.nickname]
            bcommand = BlockCommand(self.app, theplayer)
            theplayer.current_move = bcommand
                
    def com_halt(_self, self, args):
        """Stop the current move."""
        theplayer = self.app.game.fighters[self.nickname]
        thechar = theplayer.character
        if self.app.game.is_ready(self.nickname):
            self.app.tell(self.nickname,"You're not doing anything yet!")
        else:
            self.app.signals['game_msg'].emit("%s stops doing '%s'." % (self.nickname, theplayer.current_move.name))
            theplayer.ready = True
            theplayer.current_move = None
            self.app.signals['game_msg'].emit(theplayer.status_msg)
            
    def com_moves(_self, self, args):
        """Show a list of moves for your character."""
        theplayer = self.app.game.fighters[self.nickname]
        thechar = theplayer.character
        themoves = self.app.database.get_moves_for(thechar.selector)
        self.app.tell(self.nickname,
        "%s's moves are :" % thechar.fullname)
        for move in themoves:
            self.app.tell(self.nickname, 
            "%s(%s) , %d , %s , %s , CanSpr:%s, CanCtr:%s" % (
            move.fullname, move.selector, move.power,
            move.element, move.target, move.cansuper, move.cancounter))

exported_class = BattleContext
