from urb import commands
from urb.util import dlog

class BuilderCommand(commands.Command):
    """
Enter build mode and access commands for desiging game assets.
"""

    adminlevel = commands.BUILDER
    
    def perform(self):
        self.player.session.switch('builder')
        self.alive = False

exported_class = BuilderCommand
