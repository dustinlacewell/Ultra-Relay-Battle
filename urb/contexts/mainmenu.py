from urb import contexts, commands
from urb.colors import colorize
from urb.util import dlog, metadata

class MainMenuContext(contexts.Context):
    """You are at the main-menu."""
    allowed = ['minigames']
    
    def enter(_self, self):
        self.app.game.on_command(self.player, 'all', [])   

exported_class = MainMenuContext
