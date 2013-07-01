from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class StartBattleCommand(commands.Command):
    """
Force the battle to begin.
"""

    adminlevel = commands.MODERATOR

    def perform(self):
        if self.app.game:
            if self.app.game.state == "selection":
                self.session.msg("Character selection is still open. (closeselect)")
            elif self.app.game.state == "battle":
                self.session.msg("The battle has already started.")
            else:
                self.app.game.start_battle()
        else:
            self.session.msg("There is no battle to start. (openselect)")
            
exported_class = StartBattleCommand
