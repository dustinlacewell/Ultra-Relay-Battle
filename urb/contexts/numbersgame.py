from urb import contexts
from urb.colors import colorize
from urb.util import dlog, metadata

class CustomContext(contexts.Context):
    """
This context is used for testing various features of the internal features of
the game. Its behavior is undefined. Check the source if you are unsure.
"""
        
    def enter(_self, self):
        self.app.game.do_help(self.nickname, 'help', [])  
            
    def com_exit(_self, self, args):
        """Exit back to the main-menu."""
        self.switch('mainmenu')         
    
    def com_test(_self, self, args):
        """Who knows?"""
           

exported_class = CustomContext
