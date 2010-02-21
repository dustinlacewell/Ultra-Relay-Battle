from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class NoticeCommand(commands.Command):
    """
A global message sent to all connected sessions and both channels.
"""

    adminlevel = commands.MODERATOR

    schema = (('msg','message'), )
    def perform(self):
        msg = '<red>%s:<black> %s' % ('NOTICE', self.args['message'])
        self.app.signals['global_msg'].emit(msg)

exported_class = NoticeCommand
