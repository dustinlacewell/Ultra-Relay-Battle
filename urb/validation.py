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
from urb.characters.choices import ELEMENTS
from urb import contexts
from urb.players.models import Player
from urb.characters.models import Character, Move
from urb.util import dlog, dtrace, slug_to_int, int_to_slug

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
    elements = [e[0] for e in ELEMENTS]
    if etype not in elements:    
        choices = [e for e in elements if e.startswith(etype)]
        raise ValidationError("'%s' is not a valid element." % etype, element, choices)
    else:
        return etype, argsleft
    
def game(app, name, argsleft):
    """Validate argument to an open game."""
    game_slug = argsleft.pop(0)
    try: 
        _game = app.games[slug_to_int(game_slug)]
        return _game, argsleft
    except (KeyError, TypeError):
        choices = [k for k in app.games if k.startswith(game_slug)]
        raise ValidationError("'%s' is not an available game." % game_slug, game, choices)
        
def gametype(app, name, argsleft):
    """Validate argument to an open game."""
    game_type = argsleft.pop(0)
    try: 
        _game_type = GameType.objects.get(selector=game_type)
        return _game, argsleft
    except GameType.DoesNotExist:
        choices = GameType.objects.filter(selector__startswith=game_type)
        raise ValidationError("'%s' is not an available game." % game_type, gametype, choices)
        
def player(app, name, argsleft):
    """Validate argument to a logged on player."""
    username = argsleft.pop(0)
    try: 
        _player = Player.objects.get(username=username)
        return _player, argsleft
    except Player.DoesNotExist:
        choices = Player.objects.filter(
            username__startswith=username,
        )
        raise ValidationError("'%s' is not currently signed on." % username, player, choices)
        
def character(app, name, argsleft):
    """Validate argument to an existing character."""
    selector = argsleft.pop(0)
    try: 
        _character = Character.objects.get(selector=selector)
        return _character, argsleft
    except Character.DoesNotExist:
        choices = Character.objects.filter(selector__startswith=selector)
        raise ValidationError("'%s' is not a valid character selector." % selector, character, choices)
    
def cattr(app, name, argsleft):
    """Validate argument to an attribute on a character."""
    attrname = argsleft.pop(0)
    if attrname in Character.vorder:
        return attrname, argsleft
    else:
        choices = [a for a in Character.vorder if a.startswith(attrname)]
        raise ValidationError("'%s' is not a valid character attribute." % attrname, cattr, choices)
        
def move(app, name, argsleft, char_selector=None):
    """Validate argument to a *LIST* of existing moves."""
    selector = argsleft.pop(0)
    kwargs = {'selector':selector}
    if char_selector:
        char = Character.objects.get(selector=char_selector)
        kwargs['character'] = char
    moves = Move.objects.filter(**kwargs)
    if len(moves):
        return moves[0], argsleft
    else:
        del kwargs['selector']
        kwargs['selector__startswith'] = selector
        choices = Move.objects.filter(**kwargs)
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
    from urb.gametypes.models import GameType

    selector = argsleft.pop(0)
    try: 
        gt = GameType.objects.get(selector=selector)
        return gt, argsleft
    except GameType.DoesNotExist:
        choices = GameType.objects.filter(selector__startswith=selector)
        raise ValidationError("'%s' is not a valid gametype." % selector, gametype, choices)
    
def gattr(app, name, argsleft):
    """Validate argument to an attribute on a gametype."""
    from urb.gametypes.models import GameType

    attrname = argsleft.pop(0)
    if attrname in GameType.vorder:
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
        
        'game':game,
        'player':player,
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
                        validated[name], argsleft = vfunc(app, name, argsleft, char_selector=last_vchar.selector)
                    elif rawtype == 'char':
                        validated[name], argsleft = vfunc(app, name, argsleft)
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
            

