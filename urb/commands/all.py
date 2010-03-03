from textwrap import wrap

from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata
from urb.constants import MLW

class AllCommand(commands.Command):
    """
Lists all commands (including globals) that are available to you.
"""
    adminlevel = commands.PLAYER
    
    def perform(self):
        clocals, cglobals = commands.get_allowed(self.player) 
        clocals = ", ".join(clocals)
        cglobals = ", ".join(cglobals)
        if clocals and cglobals:
            listing = clocals + ", " + cglobals
        else:
            listing = clocals if clocals else cglobals if cglobals else ""
        self.player.tell("ALL COMMANDS", fmt="-<")
        for line in wrap(listing, self.player.linewidth):
            self.player.tell(line)

exported_class = AllCommand
