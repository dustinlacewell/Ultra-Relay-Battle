from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class CloseSelectionCommand(commands.Command):
    """
Close character selection so battle may begin.
"""

    adminlevel = commands.MODERATOR

    def perform(self):
        if self.app.game.state == "idle":
            self.app.tell(self.player.nickname,
            "Character selection isn't open.")
        elif self.app.game.state == "prebattle":
            self.app.tell(self.player.nickname,
            "Character selection already closed.")
        elif self.app.game.state == "battle":
            self.app.tell(self.plaer.nickname,
            "You can't open selection during battle.")
        else:
            self.app.signals['close_selection'].emit()
                        
        
            
exported_class = CloseSelectionCommand
