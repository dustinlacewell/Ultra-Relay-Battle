import random
import math

from urb import contexts, commands, validation
from urb.colors import colorize
from urb.util import dlog, metadata
from urb.constants import *

class BlockCommand(commands.Command):
    def __init__(self, app, player):
        self.app = app
        self.player = player
        self.target = None
        self.app.signals['game_msg'].emit(self.app.game.parse_message(
            self.player, player.character.block_begin_msg))
        
    def _get_name(self):
        return 'Block'
    name = property(_get_name)


class BattleCommand(commands.Command):
    
    def __init__(self, app, player, move, target, mpcost=0, super=0):
        self.app = app
        self.player = player
        self.move = move
        self.target = target
        self.mpcost = mpcost
        self.super = super
        self.alive =  True
        
        self.tick_delay = int(self.move.power / 10)
        if super:
            prepare_msg = self.app.game.parse_message(self.player, self.move.supr_prepare_msg, target=target)
            prepare_msg = ("L%d SUPER ~ " % super) + prepare_msg
        else:
            prepare_msg = self.app.game.parse_message(self.player, self.move.prepare_msg, target=target)
        self.app.signals['game_msg'].emit(prepare_msg)
        
    def _get_name(self):
        return self.move.fullname
    name = property(_get_name)
    
        
    def perform(self):
        self.app.signals['battle_execute'].emit(self)
        
        if self.target.health <= 0:
            death_msg = self.parse_message(self.target, self.target.character.death_msg, self.player)
            self.app.signals['game_msg'].emit(death_msg)
            self.app.signals['game_msg'].emit(
            "Death slaps a sticker on %s, \"Kaput!\", you're dead. [%d]" % (
            target, target.health))
        winid = self.app.game.check_win_condition()
        if winid != None:
            self.app.signals['battle_finish'].emit(winid)
        else:
            self.player.current_move = None
            self.app.signals['game_msg'].emit(self.player.status_msg)
            
class BattleContext(contexts.Context):
    """You're in battle!"""    
    
    def on_input(_self, self, command, args):
        thechar = self.player.character
        themoves = self.app.database.get_moves_for(thechar.selector)
        super = 0
        if '*' in command:
            try:
                command, super = command.split('*')
                super = int(super)
                if super > self.app.game.settings.maxsuperlevel:
                    self.app.tell(self.player, "The max super-level is currently: %d" % self.app.game.settings.maxsuperlevel)
                    return True
            except:
                self.app.tell(self.player,
                   "Your command couldn't be parsed. If supering, your move should look like 'fireball*3'.")

        for move in themoves:
            if move.selector == command:
                if self.app.game.is_paused():
                    self.app.tell(self.player,
                    "The battle is paused, you'll have to wait to '%s'." % command)
                    return True
                elif self.player.health <= 0:
                    self.app.tell(self.player,
                    "You can't do '%s' when you're DEAD!" % move.fullname)
                    return True
                elif not self.app.game.is_ready(self.player):
                    if self.player.current_move.target:
                        self.app.tell(self.player,
                        "You can't do '%s' while you're doing '%s' on %s." % (
                        command, self.player.current_move.name,
                        self.player.current_move.target))
                    else:
                        self.app.tell(self.player,
                        "You can't do '%s' while you're doing '%s'." % (
                        command, self.player.current_move.name))
                    return True
                elif self.app.game.is_ready(self.player):
                    targetname = None
                    if len(args) >= 1:
                        targetname = args[0]
                    else:
                        targetname = self.app.game.get_target(self.player, move.target).nickname
                        if not targetname:
                            self.app.tell(self.player,
                            "You couldn't find a valid target!")
                            return True
                    try:
                        target = self.app.game.fighters[targetname]
                        self.app.game.validate_target(self.player, target, move)
                    except validation.ValidationError, e:
                        self.app.tell(self.player, e.message)
                        return True
                    else:
                        if super > 0:
                            if not move.cansuper:
                                self.app.tell(self.player, "The '%s' move can't be supered." % (move.fullname))
                                return True
                            if self.player.superpoints < super * 100:
                                self.app.tell(self.player, "You don't have enough Super to do a level %d '%s'!" % (super, move.fullname))
                                return True

                        mpcost = 0
                        if move.element != 'physical':
                            mpcost = math.ldexp(move.power, 1) / math.log(6000) * 10
                            if self.player.magicpoints < mpcost:
                                self.app.tell(self.player, "You don't have enough Magic to do '%s'!" % move.fullname)
                                return True
                        bcommand = BattleCommand(self.app, self.player, move, target, mpcost, super)
                        self.app.signals['battle_command'].emit(bcommand)
                        return True
                    
    def com_exit(_self, self, args):
        """Cancel battle participation."""
        self.app.signals['forfeit'].emit(self.player)
                        
    def com_roster(_self, self, args):
        """Get the current battle roster."""
        self.app.tell(self.player,
        " - The current battle-roster -")
        for nick, player in self.app.game.fighters.iteritems():
            char = player.character.fullname if player.character else "NO CHAR"
            self.app.tell(self.player,
            "%s(%s) - %d HP : %d MP : %d SP %s" % (
            nick, char,  player.health, 
            player.magicpoints, player.superpoints, ": READY" if player.ready else ""))
    
    @metadata(schema=(('fighter*', 'nickname'),))           
    def com_status(_self, self, args):
        """Get the status for a player or yourself."""
        if 'nickname' in args:
            self.app.tell(self.player, args['nickname'].status_msg)
        else:
            self.app.tell(self.player, self.player.status_msg)
            
    def com_block(_self, self, args):
        """Block any incomming attacks."""
        if self.app.game.is_ready(self.player):
            bcommand = BlockCommand(self.app, self.player)
            self.player.current_move = bcommand
                
    def com_halt(_self, self, args):
        """Stop the current move."""
        self.player.halt()
            
    def com_moves(_self, self, args):
        """Show a list of moves for your character."""
        thechar = self.player.character
        themoves = self.app.database.get_moves_for(thechar.selector)
        self.app.tell(self.player,
        "%s's moves are :" % thechar.fullname)
        for move in themoves:
            self.app.tell(self.player, move.info)

exported_class = BattleContext
