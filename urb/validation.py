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
from urb.db import *
from urb.commands import get_name
from urb.constants import elements
from urb import contexts

from urb.util import dlog, dtrace

class ValidationError(Exception):
    def __init__(self, message, validator, choices=[]):
        self.message = message
        self.validator = validator
        self.choices = choices
        
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
        raise ValidationError("'%s' must be an integer." % name, integer)
    else:
        return val, argsleft
        
def floating(app, name, argsleft):
    """Convert argument to float."""
    try:
        val = float(argsleft.pop(0))
    except ValueError:
        raise ValidationError("'%s' must be an float." % name, floating)
    else:
        return val, argsleft
        
        
def string(app, name, argsleft):
    """An ordinary string argument."""
    return unicode(argsleft.pop(0)), argsleft

def element(app, name, argsleft):
    """Validate argument to an element."""
    etype = argsleft.pop(0)
    if etype not in elements:    
        choices = [e for e in elements if e.startswith(etype)]
        raise ValidationError("'%s' is not a valid element." % etype, element, choices)
    else:
        return etype, argsleft
    
def user(app, name, argsleft):
    """Validate argument to an existing user."""
    nick = argsleft.pop(0)
    user = User.get(nickname=nick)
    if not user:
        choices = [n.nickname for n in User.all() if n.nickname.startswith(nick)]
        raise ValidationError("'%s' is not a valid user." % nick, user, choices)
    else:
        return user, argsleft
        
def player(app, name, argsleft):
    """Validate argument to a logged on player."""
    nick = argsleft.pop(0)
    try:
        plrobj = app.game.players[nick]
    except KeyError:
        choices = [p.nickname for p in app.game.players.iterkeys() if p.nickname.startswith(nick)]
        raise ValidationError("'%s' is not currently signed on." % nick, player, choices)
    else:
        return plrobj, argsleft
        
def fighter(app, name, argsleft):
    """Validate argument to a fighting player."""
    nick = argsleft.pop(0)
    try:
        plrobj = app.game.fighters[nick]
    except KeyError:
        choices = [f.nickname for f in app.game.fighters.itervalues() if f.nickname.startswith(nick)]
        raise ValidationError("'%s' is not an active fighter." % nick, fighter, choices)
    else:
        return plrobj, argsleft
        
def character(app, name, argsleft, player=None):
    """Validate argument to an existing character."""
    selector = argsleft.pop(0)
    kwargs = {'selector':selector}
    if player and not isinstance(player.session.context,  contexts.get('builder')):
        kwargs['finalized'] = 1
    char = Character.filter(**kwargs)
    if char:
        return char[0], argsleft
    else:
        del kwargs['selector']
        choices = [c.selector for c in Character.filter(**kwargs) if c.selector.startswith(selector)]
        raise ValidationError("'%s' is not a valid character selector." % selector, character, choices)
    
def cattr(app, name, argsleft):
    """Validate argument to an attribute on a character."""
    attrname = argsleft.pop(0)
    if attrname in Character.vorder:
        return attrname, argsleft
    else:
        choices = [a for a in Character.vorder if a.startswith(attrname)]
        raise ValidationError("'%s' is not a valid character attribute." % attrname, cattr, choices)
        
def move(app, name, argsleft, char=None):
    """Validate argument to a *LIST* of existing moves."""
    selector = argsleft.pop(0)
    kwargs = {'selector':selector}
    if char:
        kwargs['ownerselector'] = char.selector
    moves = Move.filter(**kwargs)
    if len(moves):
        return moves, argsleft
    else:
        del kwargs['selector']
        choices = [m.selector for m in Move.filter(**kwargs) if m.selector.startswith(selector)]
        raise ValidationError("'%s' is not a valid move selector." % selector, move, choices)
    
def mattr(app, name, argsleft):
    """Validate argument to an attribute on a move."""
    attrname = argsleft.pop(0)
    if attrname in Move.vorder:
        return attrname, argsleft
    else:
        choices = [a for a in Move.vorder if a.startswith(attrname)]
        raise ValidationError("'%s' is not a valid move attribute." % attrname, mattr, choices)
        
def gametype(app, name, argsleft):
    """Validate argument to an existing gametype."""
    from urb import gametypes
    typename = argsleft.pop(0)
    gt = gametypes.get(typename)
    if gt:
        gt = GameSettings.get(selector=typename)
        if gt == None:
            gt = GameSettings.create(selector=typename)
        return gt, argsleft
        
    else:
        choices = [g.selector for g in GameSettings.all() if g.selector.startswith(typename)]
        raise ValidationError("'%s' is not a valid gametype." % typename, gametype, choices)
    
def gattr(app, name, argsleft):
    """Validate argument to an attribute on a gametype."""
    attrname = argsleft.pop(0)
    if attrname in GameSettings.vorder:
        return attrname, argsleft
    else:
        choices = [a for a in GameSettings.vorder if a.startswith(attrname)]
        raise ValidationError("'%s' is not a valid gametype attribute." % attrname, gattr, choices)
        
## END VALIDATORS ##

types = {
        
        'int':integer, 
        'float':floating,
        'str':string, 
        'msg':message, 
        
        'user':user, 
        'player':player, 'fighter':fighter,
        'char':character, 'cattr':cattr,
        'move':move, 'mattr':mattr,
        'gtype':gametype, 'gattr':gattr, 
        'element':element,
    }


def command(app, comobj, arguments, player=None):
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
    # the validated arugments
    validated = {}
    # the last character validated
    last_vchar = None
    # arguments left to process
    argsleft = list(arguments)
    # only validate if need to
    if hasattr(comobj, 'schema'):
        # argument count
        idx = 0
        # process each schema arugment
        for type, name in comobj.schema:
            idx += 1
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
                        raise ValidationError("Missing '%s' parameter." % name, None)
                else:
                    # grab the right validator
                    vfunc = types[rawtype]
                    # store valid arg and remaining args
                    if last_vchar and rawtype == 'move':
                        validated[name], argsleft = vfunc(app, name, argsleft, char=last_vchar)
                    elif rawtype == 'char':
                        validated[name], argsleft = vfunc(app, name, argsleft, player=player)
                    else:
                        validated[name], argsleft = vfunc(app, name, argsleft)
                    if rawtype == 'char':
                        last_vchar = validated[name]
            # on validation error, append index:type tag
            except ValidationError, e:
                if rawtype == 'move' and last_vchar:
                    e.message = "{0} for {1}.".format(e.message[:-1], last_vchar.selector)
                tag = " (%d:%s)" % (len(validated) + 1, type)
                e.message = e.message + tag
                e.argnum = idx
                # reraise modified Validation Error
                raise e
        # return validated arugment dictionary
        return validated
            

