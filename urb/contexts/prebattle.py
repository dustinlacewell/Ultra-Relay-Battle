from urb import contexts, commands
from urb.colors import colorize
from urb.util import dlog, metadata

class PreBattleContext(contexts.Context):
    """
                    You are waiting for battle.
            'chars'    =    Get a listing of characters.
            'pick'     =    Pick a character e.g. : pick testman
            'ready'    =    Toggle your ready status
                 
                 Use help for additional support.   
"""
    
    def enter(_self, self):
        for line in _self.__doc__.split('\n'):
            self.player.tell(line)

    def com_exit(_self, self, args):
        """Cancel battle participation."""
        _self.com_oops(self, {})
        self.app.signals['forfeit'].emit(self.player)
            
    @metadata(adminlevel=commands.PLAYER, schema=(('char','selector'),))
    def com_pick(_self, self, args):
        """Pick a character to fight with."""
        if args['selector'].finalized == 0:
            self.player.tell("'%s' is not a valid character selector." % args['selector'].selector)
        else:
            self.app.signals['choose'].emit(self.player, args['selector'].selector)
            self.player.tell("Make sure to 'ready' up if you're prepared for battle.")
        
    def com_oops(_self, self, args):
        """Forget your current character selection."""
        if self.player.character and not self.player.ready:
            self.app.signals['game_msg'].emit(
            "%s decides not to play as %s" % (self.player, self.player.character.fullname))
            self.player.character = None
            self.player.current_move = None
        elif self.app.game.state in ['prebattle']:
            self.player.tell("You can't do that now, battle is about to begin!")

    def com_roster(_self, self, args):
        """Get the current battle roster."""
        self.player.tell(" - The current battle-roster -")
        for nick, player in self.app.game.fighters.iteritems():
            char = player.character.fullname if player.character else "NO CHAR"
            self.player.tell("%s(%s) - %d HP : %d MP : %d SP %s" % (
            nick, char,  player.health, 
            player.magicpoints, player.superpoints, ": READY" if player.ready else ""))
            
    def com_ready(_self, self, args):
        """Toggle whether you're ready for battle to begin."""
        if self.app.game.state in ['prebattle']:
            self.player.tell("You can't do that now, battle is about to begin!")
        else:
            self.app.signals['ready'].emit(self.player)
            
    def com_moves(_self, self, args):
        """Show a list of moves for your character."""
        thechar = self.player.character
        if thechar:
            themoves = char.moves
            self.player.tell("%s's moves are :" % thechar.fullname)
            for move in themoves:
                self.player.tell(move.info)
        else:
            self.player.tell("You haven't selected a character yet.")
            
exported_class = PreBattleContext
