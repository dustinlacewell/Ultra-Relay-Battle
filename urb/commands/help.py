from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class HelpCommand(commands.Command):
    """
The 'help' command takes an single optional argument. The argument can contain
the name of command that you would like to get help on. 'help' will include
the correct format for using the command and any relevant information. A 
command's format may look like:

setadmin [nickname] [adminlevel]

This says setadmin requires two passed values. If you forget values or pass
values of the wrong type (letters when numbers were expected) URB will let you
know. Arguments with an asterisk(*) are optional.

Using 'help' with NO arguments will show help for the current context you're in
and any commands that are available to you.

The 'all' command will show all available commands including globally available
commands.

See INFO for: commands, contexts
"""

    adminlevel = commands.PLAYER
    schema = (('str*','command'), )
    
    def perform(self):
        allowed = commands.get_allowed(self.player, all=True)
        context = self.player.session.context
        try: command = self.args['command']
        except KeyError:
            if context.__doc__:
                for line in context.__doc__.split('\n'):
                    self.app.tell(self.player.nickname, line)
                self.app.tell(self.player.nickname,
                "- The following commands are available -")
                available = commands.get_allowed(self.player, all=False)
                available = ['help', 'all'] + available
                available = ", ".join(available)
                while available:
                    send, available = available[:435], available[436:]
                    self.app.tell(self.player.nickname, send)
        else:
            comobj = None
            if command in allowed:
                try:
                    comobj = getattr(context, "com_%s" % command)
                except:
                    comobj = commands.get(command)
                finally:
                    if comobj:
                        if comobj.__doc__ or hasattr(comobj, 'schema'):
                            for line in commands.get_help(comobj):
                                self.app.tell(self.player.nickname, line)
                        else:
                            self.app.tell(self.player.nickname,
                            "Sorry, no help is available for '%s'." % command)
                    else:
                        self.app.tell(self.player.nickname,
                        "Sorry, %s is not a command." % command)

exported_class = HelpCommand
