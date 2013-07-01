from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class CloseSelectionCommand(commands.Command):
    """
Close character selection so battle may begin.
"""

    adminlevel = commands.MODERATOR

    def perform(self):
        if self.app.game:
            if self.app.game.state == "idle":
                self.session.msg("Character selection isn't open.")
            elif self.app.game.state == "prebattle":
                self.session.msg("Character selection already closed.")
            elif self.app.game.state == "battle":
                self.session.msg("You can't open selection during battle.")
            else:
                self.app.game.close_selection()
        else:
            self.session.msg(" * Character selection isn't open.")
                        
        
            
exported_class = CloseSelectionCommand
