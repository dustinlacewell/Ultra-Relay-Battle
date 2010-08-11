import random
import math

from urb import contexts, commands, validation
from urb.colors import colorize
from urb.util import dlog, metadata, render, word_table
from urb.constants import *

class BlockCommand(commands.Command):
    def __init__(self, app, player):
        self.app = app
        self.player = player
        self.target = None
        self.app.fsay(render(player.character.block_begin_msg, self.player))
        
    def _get_name(self):
        return 'block'
    name = property(_get_name)


class BattleCommand(commands.Command):
    
    def __init__(self, app, player, move, target, delay, super=0):
        self.app = app
        self.player = player
        self.move = move
        self.target = target
        self.mpcost = move.mpcost
        self.super = super
        self.alive =  True        
        self.tick_delay = delay

        
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
        self.player.tell(" - The current battle-roster - ", fmt=" ^")
        parts = []
        for nick, player in self.app.game.fighters.iteritems():
            char = player.character.fullname if player.character else "NO CHAR"
            parts.append("%s(%s)" % (nick, char))
            parts.append("  -  %d HP : %d MP : %d SP %s" % (player.health, player.magicpoints, player.superpoints, ": READY" if player.ready else ""))
            lines = word_table(parts, 2, fmt=" <")
        for line in lines:
            self.player.tell(line)
    
    @metadata(schema=(('fighter*', 'nickname'),))           
    def com_status(_self, self, args):
        """Get the status for a player or yourself."""
        if 'nickname' in args:
            self.player.tell(args['nickname'].status_msg)
        else:
            self.player.tell(self.player.status_msg)
            
    def com_block(_self, self, args):
        """Block any incomming attacks."""
        # check for move prevention: stun
        if 'stun' in self.player.effects:
            self.player.tell(self.player.effects['stun'].get_denial('block'))
        elif self.player.ready:
            bcommand = BlockCommand(self.app, self.player)
            self.player.current_move = bcommand
        else:
            if self.player.current_move.target:
                self.player.tell("* You can't block while you're doing '%s' on %s." % (
                self.player.current_move.name,
                self.player.current_move.target))
            else:
                self.player.tell("* You can't block while you're doing '%s'." % (
                self.player.current_move.name))           
                
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
