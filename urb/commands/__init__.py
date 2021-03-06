import sys
from textwrap import wrap

from urb import imports
from urb.util import dlog
from urb.constants import MLW

PLAYER = 0
BUILDER = 80
MODERATOR = 90
ADMIN = 100

class Command(object):
    # default required admin level
    adminlevel = PLAYER
    # default to no associated delay
    tick_delay = None
    # Set to False right before perform is called,
    # commands can set this to True to persist for
    # an additional tick.
    alive = False

    def __init__(self, app, player, args):
        # save reference to application
        self.app = app
        # save reference to player object
        self.player = player
        # save reference to validated arguments
        self.args = args

    def verify(self):
        """Perform verification after validation before command submission"""
        pass

    def perform(self):
        pass
        
def get( command_name ):
    """Return the command class for the given command-name."""
    return imports.get('commands', command_name)
    
def get_allowed(player):
    """
    Return a list command classes a player can run in their current context based
    on admin level. all designates non-contextual commands should be included.
    Note: causes all commands to be loaded.
    """
    callowed = []
    cglobals = []
    adminlevel = player.user.adminlevel
    for name, comobj in player.session.context.get_commands().iteritems():
            if not hasattr(comobj, 'adminlevel') or comobj.adminlevel <= adminlevel:
                callowed.append(name)
    for name, comobj in imports.load_all('commands').iteritems():
        if not hasattr(comobj, 'adminlevel') or comobj.adminlevel <= adminlevel:
            cglobals.append(name)
    return callowed, cglobals
    
def get_name(comobj):
    """Get a command identifier for arbitrary command type."""
    # If metadata provides a name
    if hasattr(comobj, 'name'):
        return comobj.name
    # If contextual command
    elif comobj.__name__.startswith('com_'):
        return comobj.__name__[4:]
    # If dynamic global
    elif isinstance(comobj, object.__class__.__class__):
        path = sys.modules[comobj.__module__].__file__
        return path.split('/')[-1].split('.')[0]
    # all hope is lost
    else:   
        return "????"
        
def get_help(comobj):
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
                for line in wrap(wline, MLW, initial_indent=''):
                    helplines.append(line)
            else:
                helplines.append(wline)
        
    # if command has a schema
    if hasattr(comobj, 'schema'):
        # schema line starts with command-name
        schemaline = "%s " % get_name(comobj)
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
                helplines[idx] = "%s : %s" % (get_name(comobj), helplines[idx])
                break
    
    return helplines
        
def refresh( command_name ):
    """Reload the module supporting the given command."""
    return imports.refresh(command_name)



