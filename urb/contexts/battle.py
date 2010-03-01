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
        self.app.game.battle_do(self)
            
class BattleContext(contexts.Context):
    """You're in battle!"""    
    
    def on_input(_self, self, command, args):
        return self.app.game.process_battle_input(self.player, command, args)
                    
    def com_exit(_self, self, args):
        """Cancel battle participation."""
        self.app.game.player_forfeit(self.player)
                        
    def com_roster(_self, self, args):
        """Get the current battle roster."""
        self.player.tell(" - The current battle-roster -")
        for nick, player in self.app.game.fighters.iteritems():
            char = player.character.fullname if player.character else "NO CHAR"
            self.player.tell("%s(%s) - %d HP : %d MP : %d SP %s" % (
            nick, char,  player.health, 
            player.magicpoints, player.superpoints, ": READY" if player.ready else ""))
    
    @metadata(schema=(('fighter*', 'nickname'),))           
    def com_status(_self, self, args):
        """Get the status for a player or yourself."""
        if 'nickname' in args:
            self.player.tell(args['nickname'].status_msg)
        else:
            self.player.tell(self.player.status_msg)
            
    def com_block(_self, self, args):
        """Block any incomming attacks."""
        if self.player.ready:
            bcommand = BlockCommand(self.app, self.player)
            self.player.current_move = bcommand
                
    def com_halt(_self, self, args):
        """Stop the current move."""
        self.player.halt()
            
    def com_moves(_self, self, args):
        """Show a list of moves for your character."""
        thechar = self.player.character
        themoves = thechar.moves
        self.player.tell("%s's moves are :" % thechar.fullname)
        for move in themoves:
            self.player.tell(move.info)

exported_class = BattleContext
