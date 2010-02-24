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
            self.app.tell(self.nickname, line)

    def com_exit(_self, self, args):
        """Cancel battle participation."""
        _self.com_oops(self, {})
        self.app.signals['forfeit'].emit(self.nickname)
            
    @metadata(adminlevel=commands.PLAYER, schema=(('char','selector'),))
    def com_pick(_self, self, args):
        """Pick a character to fight with."""
        if args['selector'].finalized == 0:
            self.app.tell(self.nickname, "'%s' is not a valid character selector." % args['selector'].selector)
        else:
            self.app.signals['choose'].emit(self.nickname, args['selector'].selector)
            self.app.tell(self.nickname, "Make sure to 'ready' up if you're prepared for battle.")
        
    def com_oops(_self, self, args):
        """Forget your current character selection."""
        theplayer = self.app.game.fighters[self.nickname]
        if theplayer.character and not theplayer.ready:
            self.app.signals['game_msg'].emit(
            "%s decides not to play as %s" % (self.nickname, theplayer.character.fullname))
            theplayer.character = None
            theplayer.current_move = None
        elif self.app.game.state in ['prebattle']:
            self.app.tell(self.nickname, "You can't do that now, battle is about to begin!")

    def com_roster(_self, self, args):
        """Get the current battle roster."""
        self.app.tell(self.nickname,
        " - The current battle-roster -")
        for nick, player in self.app.game.fighters.iteritems():
            char = player.character.fullname if player.character else "NO CHAR"
            self.app.tell(self.nickname,
            "%s(%s) - %d HP : %d MP : %d SP %s" % (
            nick, char,  player.health, 
            player.magicpoints, player.superpoints, ": READY" if player.ready else ""))
            
    def com_ready(_self, self, args):
        """Toggle whether you're ready for battle to begin."""
        if self.app.game.state in ['prebattle']:
            self.app.tell(self.nickname, "You can't do that now, battle is about to begin!")
        else:
            self.app.signals['ready'].emit(self.nickname)
            
    def com_moves(_self, self, args):
        """Show a list of moves for your character."""
        theplayer = self.app.game.fighters[self.nickname]
        thechar = theplayer.character
        if thechar:
            themoves = self.app.database.get_moves_for(thechar.selector)
            self.app.tell(self.nickname,
            "%s's moves are :" % thechar.fullname)
            for move in themoves:
                self.app.tell(self.nickname, move.info)
        else:
            self.app.tell(self.nickname,
            "You haven't selected a character yet.")
            
exported_class = PreBattleContext
