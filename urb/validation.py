"""
    validation.py
    
    This module is responsible for converting user command parts
    into their respective data-types. Aside from elementary
    types such as string and float validation types that
    represent entries in the database exist. For these types,
    such as a move or item, the validation requires the input
    actually corresponds to an entry existing in the database.
    
    Each validator takes the name of the argument it is
    validating and all of the argument strings left to
    process. Each validator returns a two item tuple containing
    the valid value and any argument strings not consumed or 
    throws a ValidationError. Most validators consume a single 
    string however this is not required. In the case of 
    'message' all strings are consumed and concatenated to 
    form the validated value.
    """

from urb.commands import get_name
from urb.constants import elements

from urb.util import dlog, dtrace

class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return repr(self.message)   

## BEGIN VALIDATORS ##
def message(app, name, argsleft):
    """Consume all arguments to a space delimited message."""
    return unicode(u" ".join(argsleft)), []
    
    
def integer(app, name, argsleft):
    """Convert argument to integer."""
    try:
        val = int(argsleft.pop(0))
    except ValueError:
        raise ValidationError("'%s' must be an integer." % name)
    else:
        return val, argsleft
        
def floating(app, name, argsleft):
    """Convert argument to float."""
    try:
        val = float(argsleft.pop(0))
    except ValueError:
        raise ValidationError("'%s' must be an float." % name)
    else:
        return val, argsleft
        
        
def string(app, name, argsleft):
    """An ordinary string argument."""
    return unicode(argsleft.pop(0)), argsleft

def element(app, name, argsleft):
    """Validate argument to an element."""
    etype = argsleft.pop(0)
    if etype not in elements:    
        raise ValidationError("'%s' is not a valid element." % etype)
    else:
        return etype, argsleft
    
def user(app, name, argsleft):
    """Validate argument to an existing user."""
    nick = argsleft.pop(0)
    user = app.database.get_user(nick)
    if not user:    
        raise ValidationError("'%s' is not a valid user." % nick)
    else:
        return user, argsleft
        
def player(app, name, argsleft):
    """Validate argument to a logged on player."""
    nick = argsleft.pop(0)
    try:
        plrobj = app.game.players[nick]
    except KeyError:
        raise ValidationError("'%s' is not currently signed on." % nick)
    else:
        return plrobj, argsleft
        
def fighter(app, name, argsleft):
    """Validate argument to a fighting player."""
    nick = argsleft.pop(0)
    try:
        plrobj = app.game.fighters[nick]
    except KeyError:
        raise ValidationError("'%s' is not an active fighter." % nick)
    else:
        return plrobj, argsleft
        
def character(app, name, argsleft):
    """Validate argument to an existing character."""
    selector = argsleft.pop(0)
    char = app.database.get_character(selector)
    if char:
        return char, argsleft
    else:
        raise ValidationError("'%s' is not a valid character selector." % selector)
        
def move(app, name, argsleft):
    """Validate argument to a *LIST* of existing moves."""
    selector = argsleft.pop(0)
    moves = app.database.get_all_moves(selector)
    if len(moves):
        return moves, argsleft
    else:
        raise ValidationError("'%s' is not a valid move selector." % selector)
        
def gametype(app, name, argsleft):
    """Validate argument to an existing gametype."""
    from urb import gametypes
    typename = argsleft.pop(0)
    gt = gametypes.get(typename)
    if gt:
        gt = app.database.get_gametype(typename)
        return gt, argsleft
    else:
        raise ValidationError("'%s' is not a valid gametype." % typename)
        
## END VALIDATORS ##


def command(app, comobj, arguments):
    """
    urb.validation.command
        app        :    Main application reference
        comobj     :    Command object to validate against
        arguments  :    Tuple of space-split user input parts
        
    command attempts to validate all command arguments against
    the actual user input. Each Commmand object should have
    a schema associated with it which specifies its arugment
    and argument types. It handles processing optional
    arguments when * is appended to the validation type (char*).
    """
    # mapping of type keys to validators         
    types = {
        'msg':message, 'int':integer, 
        'str':string, 'user':user, 
        'player':player, 'move':move,
        'char':character, 'float':floating,
        'gtype':gametype, 'fighter':fighter,
        'element':element,
    }
    # the validated arugments
    validated = {}
    # arguments left to process
    argsleft = list(arguments)
    # only validate if need to
    if hasattr(comobj, 'schema'):
        # process each schema arugment
        for type, name in comobj.schema:
            try:
                # get raw type
                rawtype = type.strip('*')
                # get optional boolean
                optional = '*' in type
                # Auto-handle invalid argument count
                if len(argsleft) == 0:
                    # if last parameter is optional, we're done anyway
                    if optional: break 
                    else:
                        raise ValidationError("Missing '%s' parameter." % name)
                else:
                    # grab the right validator
                    vfunc = types[rawtype]
                    # store valid arg and remaining args
                    validated[name], argsleft = vfunc(app, name, argsleft)
            # on validation error, append index:type tag
            except ValidationError, e:
                tag = " (%d:%s)" % (len(validated) + 1, type)
                errmsg = e.message + tag
                # reraise modified Validation Error
                raise ValidationError(errmsg)
        # return validated arugment dictionary
        return validated
            

