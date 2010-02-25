from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class AbortBattleCommand(commands.Command):
    """
Force the battle to abort.
"""

    adminlevel = commands.MODERATOR

    def perform(self):
        if self.app.game.state == "idle":
            self.app.tell(self.player,
            "There is no battle currently.")
        elif self.app.game.state == "selection":
            self.app.tell(self.player,
            "Character selection is still open. (closeselect)")
        elif self.app.game.state == "prebattle" or self.app.game.state == "battle":
            self.app.signals['battle_abort'].emit()
            
exported_class = AbortBattleCommand
