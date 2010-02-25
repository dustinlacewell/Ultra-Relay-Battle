from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class StartBattleCommand(commands.Command):
    """
Force the battle to begin.
"""

    adminlevel = commands.MODERATOR

    def perform(self):
        if self.app.game.state == "selection":
            self.app.tell(self.player,
            "Character selection is still open. (closeselect)")
        elif self.app.game.state == "battle":
            self.app.tell(self.player,
            "The battle has already started.")
        else:
            self.app.signals['battle_start'].emit()
            
exported_class = StartBattleCommand
