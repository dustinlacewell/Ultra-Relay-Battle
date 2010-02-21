from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class AllCommand(commands.Command):
    """
Lists all commands (including globals) that are available to you.
"""
    adminlevel = commands.PLAYER
    
    def perform(self):
        allowed = commands.get_allowed(self.player, all=True) 
        allowed = ", ".join(allowed)
        context = self.player.session.context
        self.app.tell(self.player.nickname,
        "- The following commands are available -")
        while allowed:
            send, allowed = allowed[:435], allowed[436:]
            self.app.tell(self.player.nickname, send)

exported_class = AllCommand
