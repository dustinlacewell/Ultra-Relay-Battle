from urb import contexts
from urb.colors import colorize
from urb.util import dlog

class MiniGameContext(contexts.Context):
    """
Minigames - Small games to show off the session contexts.
"""
    allowed = ['numbers', 'exit'] 
        
    def enter(_self, self):
        self.app.game.on_command(self.nickname, 'help', [])
        
    def com_exit(_self, self, args):
        """Exit the minigames back to the main menu."""
        self.switch('mainmenu')  

    def com_numbers(_self, self, args):
        """Play guess-the-number from 1 to 1000. Only 8 guesses though!"""
        self.switch('numbers' )
        
        

exported_class = MiniGameContext
