from urb import commands, imports
from urb.colors import colorize
from urb.util import dlog

class TestCommand(commands.Command):
    """
Whatever the command is currently coded to do!
"""

    adminlevel = commands.PLAYER
    schema = ( ('int*', 'first'), ('int*', 'second'))
    
    def perform(self):
        self.app.tell(self.player.nickname,
        "This command is entirely useless!")

exported_class = TestCommand
