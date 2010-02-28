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
        if self.app.game:
            if self.app.game.state == "selection":
                self.app.tell(self.player,
                "Character selection is already open.")
            elif self.app.game.state == "battle":
                self.app.tell(self.player,
                "You can't open selection during battle.")
            else:
                self.app.game.on_open_selection()
        else:
            if 'gametype' in self.args:
                gtype = gametypes.get(self.args['gametype'])
                if gtype:
                    self.app.set_game(gtype)
                else:
                    self.app.tell(self.player,
                    "No such gametype exists.")
            else:
                print dir(gametypes)
                gtype = gametypes.get('survivor')
                if gtype:
                    self.app.set_game(gtype)
                else:
                    self.app.tell(self.player, "# Missing 'gametype' parameter. (1:str)")

            
exported_class = OpenSelectionCommand
