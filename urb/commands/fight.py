from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class FightCommand(commands.Command):
    """
Sign up for battle and choose a character!
"""

    adminlevel = commands.PLAYER

    def perform(self):
        if self.player.nickname in self.app.game.fighters.keys():
            self.app.tell(self.player.nickname,
            "You're already a participant in battle.")
        elif self.app.game.state == 'selection':
            self.app.signals['signup'].emit(self.player.nickname)
        else:
            self.app.tell(self.player.nickname,
            "Character selection isn't currently open right now.")
            
exported_class = FightCommand
