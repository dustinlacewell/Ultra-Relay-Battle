from urb import commands, gametypes
from urb.colors import colorize
from urb.util import dlog, metadata

class OpenSelectionCommand(commands.Command):
    """
Sign up for battle and choose a character!
"""

    adminlevel = commands.MODERATOR
    schema = (('str*','gametype'),)
    def perform(self):
        if self.app.game.state == "selection":
            self.app.tell(self.player.nickname,
            "Character selection is already open.")
        elif self.app.game.state == "battle":
            self.app.tell(self.player.nickname,
            "You can't open selection during battle.")
        else:
            if 'gametype' in self.args:
                gtype = gametypes.get(self.args['gametype'])
                if gtype:
                    self.app.signals['open_selection'].emit(gtype)
                else:
                    self.app.tell(self.player.nickname,
                    "No such gametype exists.")
            elif self.app.game.state == 'prebattle':
                self.app.signals['open_selection'].emit(None)
            else:
                self.app.tell(self.player.nickname, "# Missing 'gametype' parameter. (1:str)")

            
exported_class = OpenSelectionCommand
