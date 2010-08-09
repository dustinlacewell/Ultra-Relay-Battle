from textwrap import wrap

from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata
from urb.constants import MLW

class HelpCommand(commands.Command):
    """
The 'help' command takes an single optional argument. The argument can contain \
the name of command that you would like to get help on. 'help' will include \
the correct format for using the command and any relevant information. A \
command's format may look like:

setadmin [nickname] [adminlevel]

This says setadmin requires two passed values. If you forget values or pass \
values of the wrong type (letters when numbers were expected) URB will let you \
know. Arguments with an asterisk(*) are optional.

Using 'help' with NO arguments will show help for the current context you're in \
and any commands that are available to you.

The 'all' command will show all available commands including globally available \
commands.

See INFO for: commands, contexts
"""

    adminlevel = commands.PLAYER
    schema = (('str*','command'), )
    
    def _get_help(self, comobj):
        """
        Get the generated lines of help for a command object
        using both the validation schema and the object's
        doctring.
        """
        helplines = []
        # process the newline split docstring
        if comobj.__doc__:
            for wline in comobj.__doc__.splitlines():
                if wline.strip():
                    for line in wrap(wline, self.player.linewidth, initial_indent=''):
                        helplines.append(line)
                else:
                    helplines.append(wline)
            
        # if command has a schema
        if hasattr(comobj, 'schema'):
            # schema line starts with command-name
            schemaline = "%s " % commands.get_name(comobj)
            # process each arugment
            for arg in comobj.schema:
                type, name = arg
                if '*' in type: name = "%s*" % name
                schemaline = "%s [%s:%s]" % (schemaline, type[:1], name)
            helplines.insert(0, "-"*MLW)
            helplines.insert(0, schemaline)
            helplines.insert(0, "-"*MLW)
        else:
            for idx, line in enumerate(helplines):
                if line.strip(): 
                    helplines[idx] = "%s : %s" % (commands.get_name(comobj), helplines[idx])
                    break
        return helplines
    
    def perform(self):
        clocals, cglobals = commands.get_allowed(self.player)
        context = self.player.session.context
        try: command = self.args['command']
        except KeyError:
            if context.__doc__:
                self.player.tell("", fmt="-<")
                for wline in context.__doc__.splitlines():
                    for line in wrap(wline, self.player.linewidth):
                        self.player.tell(line)
#                self.player.tell("", fmt="-<")
                self.player.tell("AVAILABLE COMMANDS ('all' for more)", fmt="-<")
                available = ['help', 'all'] + clocals
                available = ", ".join(available)
                for line in wrap(available, self.player.linewidth):
                    self.player.tell(line)
        else:
            comobj = None
            if command in clocals+cglobals:
                try:
                    comobj = getattr(context, "com_%s" % command)
                except:
                    comobj = commands.get(command)
                finally:
                    if comobj:
                        if comobj.__doc__ or hasattr(comobj, 'schema'):
                            for line in self._get_help(comobj):
                                self.player.tell(line)
                        else:
                            self.player.tell("Sorry, no help is available for '%s'." % command)
                    else:
                        self.player.tell("Sorry, %s is not a command." % command)

exported_class = HelpCommand
