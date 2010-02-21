from urb import contexts, commands
from urb.colors import colorize
from urb.util import dlog, metadata

class MainMenuContext(contexts.Context):
    """You are at the main-menu."""
    allowed = ['minigames']
    
    def enter(_self, self):
        self.app.game.on_command(self.nickname, 'help', [])
    
    @metadata(adminlevel=commands.PLAYER)
    def com_minigames(_self, self, args):
        """Play minigames created during the development of Ultra Relay Battle."""
        self.switch('minigames')   
        
    @metadata(adminlevel=commands.ADMIN)
    def com_testing(_self, self, args):
        """Enter the testing context."""
        self.switch('testing')     

exported_class = MainMenuContext
