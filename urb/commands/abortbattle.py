from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class AbortBattleCommand(commands.Command):
    """
Force the battle to abort.
"""

    adminlevel = commands.MODERATOR

    def perform(self):
        self.app.unset_game()
            
exported_class = AbortBattleCommand
