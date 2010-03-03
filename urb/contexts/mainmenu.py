from urb import contexts, commands
from urb.colors import colorize
from urb.util import dlog, metadata

class MainMenuContext(contexts.Context):
    """You are at the main-menu."""
    allowed = ['minigames']
    
    def enter(_self, self):
        self.app.do_command(self.player, 'help', [])   

exported_class = MainMenuContext
