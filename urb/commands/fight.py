from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class FightCommand(commands.Command):
    """
Sign up for battle and choose a character!
"""

    adminlevel = commands.PLAYER
    schema=(('char*','selector'),)
    def perform(self):
        if self.app.game:
            if self.player in self.app.game.fighters:
                self.player.tell("You're already a participant in battle.")
            elif self.app.game.state == 'selection':
                if 'selector' in self.args and self.args['selector'].finalized == 0:
                    self.player.tell("'%s' is not a valid character selector." % self.args['selector'].selector)
                else:
                    self.app.game.player_signup(self.player, self.args['selector'] if self.args else None)
            else:
                self.player.tell("Character selection isn't currently open right now.")
        else:
            self.player.tell("Character selection isn't currently open right now.")
            
exported_class = FightCommand
