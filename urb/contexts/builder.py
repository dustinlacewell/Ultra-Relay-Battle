from axiom.attributes import *

from urb import contexts, db, commands, validation
from urb.colors import colorize
from urb.util import dlog, metadata
from urb.constants import *

class BuilderContext(contexts.Context):
    """
Ultra Relay Battle - BUILDER MODE

The BUILDER MODE is available for the creation of URB data assets such as
characters, moves, items, levels and others. For help on general building
concepts please refer to:

           http://ldlework.com/wiki/urb/building

"""
    def enter(_self, self):
        for line in _self.__doc__.split('\n'):
            self.app.tell(self.player, line)
            
        _self.working = None
            
    def _to_dict(_self, listobj):
        newdict = {}
        for key, val in listobj:
            newdict[key] = val
        return newdict

    def com_exit(_self, self, args):
        "Exit to the main-menu."
        self.revert()
    
    @metadata(schema=(('str','selector'), ('msg','fullname')))
    def com_mkchar(_self, self, args):
        """
Create a new character.
"""
        selector = unicode(args['selector'])
        fullname = unicode(args['fullname'])
        char = self.app.database.new_character(selector, fullname)
        if char:
            self.app.tell(self.player,
            "'%s' character succesfully created." % args['selector'])
            _self.working = char
            
    @metadata(schema=(('char','character'), ('str', 'selector'), ('msg', 'fullname')))
    def com_mkmove(_self, self, args):
        """
Create a new character move.
"""
        char = args['character']
        selector = unicode(args['selector'])
        fullname = unicode(args['fullname'])
        move = self.app.database.new_move(selector, fullname, char.selector)
        if move:
            self.app.tell(self.player,
            "'%s' move successfully created for '%s'." % (selector, char.selector))
            _self.working = char
    
    @metadata(adminlevel=100, schema=(('char', 'selector'), ))
    def com_rmchar(_self, self, args):
        """
Permanently delete character.
"""
        self.app.database.del_character(args['selector'].selector)
            
    @metadata(schema=(('char','selector'), ('msg*','filters')))
    def com_lsc(_self, self, args):
        """
Print character attributes and move selectors. Passing no filters prints all 
attributes or The filters are a list of attributes to print. The filters you 
pass in can be partial and will print any attributes that they match. Passing 
'block' would return all the block messages, for example. 
"""
        
        print list(self.app.database.dbroot['Characters'])
        char = args['selector']
        attrs =  db.CharacterProfile.vorder
        fields = attrs
        # apply autocomplete filters
        if 'filters' in args:
            newfields = []
            filters = args['filters'].split()
            for f in filters:
                for attr in attrs:
                    if attr.startswith(f):
                        newfields.append(attr)
            fields = newfields
        for field in fields:
            self.app.tell(self.player, "%s%s: %s" % (
                field, (20 - len(field)) * " ", getattr(char, field)))
                
        movelist = self.app.database.get_moves_for(char.selector)
        movelist = [move.selector for move in movelist]
        movelist = ", ".join(movelist)
        if 'filters' not in args and movelist:
            self.app.tell(self.player, "-" * 80)
            self.app.tell(self.player, "Moves: %s" % movelist)
            
    @metadata(schema=(('char','pselector'), ('str', 'mselector'), ('msg*', 'filters')))
    def com_lsm(_self, self, args):
        """
Print move attributes. Passing no filters prints all attributes or the filters 
are a list of attributes to print. The filters you pass in can be partial and 
will print any attributes that they match. Passing 'can' would return both 
the can* booleans, for example. In this command mselector can also be partial.
""" 
        char = args['pselector']
        attrs = db.MoveProfile.vorder
        fields = attrs
        mselector = args['mselector']
        movelist = self.app.database.get_moves_for(char.selector)
        themove = None
        for move in movelist:
            if move.selector.startswith(mselector):
                themove = move
        if themove:
            if 'filters' in args:
                newfields = []
                filters = args['filters'].split()
                for f in filters:
                    for attr in attrs:
                        if attr.startswith(f):
                            newfields.append(attr)
                fields = newfields
            for field in fields:
                self.app.tell(self.player, "%s%s: %s" % (
                    field, (20 - len(field)) * " ", getattr(themove, field)))
        else:
            self.app.tell(self.player,
            "'%s' mselector argument didn't match any moves on '%s'." % (mselector, char.selector))

    @metadata(schema=(('gtype','gametype'), ('msg*','filters')))
    def com_lsg(_self, self, args):
        """
Print gametype settings. Passing no filters prints all 
settings or The filters are a list of settings to print. The filters you 
pass in can be partial and will print any settings that they match. Passing 
'max' would return all the max settings, for example. 
"""
        gtype = args['gametype']
        attrs =  db.GameSettings.vorder
        fields = attrs
        # apply autocomplete filters
        if 'filters' in args:
            newfields = []
            filters = args['filters'].split()
            print repr(filters)
            for f in filters:
                for attr in attrs:
                    if attr.startswith(f):
                        newfields.append(attr)
            fields = newfields
        for field in fields:
            self.app.tell(self.player, "%s%s: %s" % (
                field, (20 - len(field)) * " ", getattr(gtype, field)))    
            
    @metadata(schema=(('gtype', 'gametype'), ('str', 'attribute'), ('msg', 'value')))
    def com_setg(_self, self, args):
        """
Set a setting on the gametype to value. Some settings require a 
certain type of value, like an number or a single word. 
"""
        
        validators = {
            'int':validation.integer,
            'str':validation.string,
            'msg':validation.message,
            'float': validation.floating,
        }
            
        gtype = args['gametype']
        attr = args['attribute']
        value = [args['value']]
        fields = []
        for field, vtype in db.GameSettings.vschema.iteritems():
            if field.startswith(attr):
                fields.append(field)

        if len(fields) > 1:
            self.app.tell(self.player, "Possible attributes: " + ", ".join(fields))
        elif len(fields) == 1:
            try:
                field = fields[0]
                vtype = db.GameSettings.vschema[field]
                validator = validators[vtype]
                val, left = validator(self.app, field, value)
            except validation.ValidationError, e:
                self.app.tell(self.player, e.message)
            else:
                setattr(gtype, field, val)
                args['filters'] = attr
                _self.com_lsg(self, args)
        else:
            self.app.tell(self.player, "Sorry, there is no gametype setting '%s'." % attr)
    
    @metadata(schema=(('char','selector'), ('str','attribute'), ('msg','value')))
    def com_setc(_self, self, args):
        """
Set an attribute on the character to value. Some attributes requires a certain
type of input, like an number or a single word. The attribute may be partial.
"""
        _self.working = args['selector']
        
        validators = {
            'int':validation.integer,
            'str':validation.string,
            'msg':validation.message,
        }
            
        char = args['selector']
        attr = args['attribute']
        value = [args['value']]
        fields = []
        for field, vtype in db.CharacterProfile.vschema.iteritems():
            if field.startswith(attr):
                fields.append(field)

        if len(fields) > 1:
            self.app.tell(self.player, "Possible attributes: " + ", ".join(fields))
        elif len(fields) == 1:
            try:
                field = fields[0]
                vtype = db.CharacterProfile.vschema[field]
                validator = validators[vtype]
                val, left = validator(self.app, field, value)
            except validation.ValidationError, e:
                self.app.tell(self.player, e.message)
            else:
                if field == 'selector':
                    self.app.database.change_character_selector(char.selector, val)
                elif field in ['pstrength', 'pdefense', 'mstrength', 'mdefense']:
                    total = char.pstrength + char.pdefense + char.mstrength + char.mdefense
                    max = MAX_CHAR_STAT_TOTAL
                    if char.weakness != 'none':
                        max += WEAKNESS_STAT_DELTA
                    if char.resistance != 'none':
                        max += RESISTANCE_STAT_DELTA
                    left = max - total
                    newtotal = val
                    if field != 'pstrength': newtotal += char.pstrength
                    if field != 'pdefense': newtotal += char.pdefense
                    if field != 'mstrength': newtotal += char.mstrength
                    if field != 'mdefense': newtotal += char.mdefense
                    
                    if max < newtotal:
                        self.app.tell(self.player, 
                        "Sorry, this character only has %d points left." % left)
                        return
                    elif val > MAX_CHAR_STAT:
                        self.app.tell(self.player,
                        "The maximum value is %d. '%s' not changed." % (MAX_CHAR_STAT, field))
                        return
                    elif val < MIN_CHAR_STAT:
                        self.app.tell(self.player,
                        "The minimum value is %d. '%s' Not changed." % (MIN_CHAR_STAT, field))
                        return
                setattr(char, field, val)
                if field != 'finalized':
                    char.finalized = 0
                args['filters'] = attr
                _self.com_lsc(self, args)
        else:
            self.app.tell(self.player, "Sorry, there is no character attribute '%s'." % attr)
       
        
    @metadata(schema=(('char', 'pselector'), ('str','mselector'), ('str', 'attribute'), ('msg', 'value')))
    def com_setm(_self, self, args):
        """
Set an attribute on the character move to value. Some attributes require a 
certain type of value, like an number or a single word. The move selector and
attribute may be partial.
"""
        validators = {
            'int':validation.integer,
            'str':validation.string,
            'msg':validation.message,
            'element': validation.element,
        }
        char = args['pselector']
        mselector = args['mselector']
        movelist = self.app.database.get_moves_for(char.selector)
        themove = None
        for move in movelist:
            if move.selector.startswith(mselector):
                themove = move
        if themove:
            attr = args['attribute']
            value = [args['value']]
            fields = []
            for field, vtype in db.MoveProfile.vschema.iteritems():
                if field.startswith(attr):
                    fields.append(field)
            if len(fields) > 1:
                self.app.tell(self.player, "Possible attributes: " + ", ".join(fields))
            elif len(fields) == 1:
                try:
                    field = fields[0]
                    vtype = db.MoveProfile.vschema[field]
                    validator = validators[vtype]
                    val, left = validator(self.app, field, value)
                except validation.ValidationError, e:
                    self.app.tell(self.player, e.message)
                    if 'element'.startswith(attr):
                        self.app.tell(self.player,"Possible elements are:")
                        self.app.tell(self.player, ", ".join(validation.elements))
                else:
                    # Additional validation
#                    if 'element'.startswith(attr):
#                        if val == 'heal':
#                            if themove.target in ['enemy', 'enemies', 'everyone']:
#                                self.app.tell(self.nickname, 
#                                "Cannot set element to '%s' when target is '%s'." % (val, themove.target))
#                                return
                    setattr(themove, field, val)
                    char.finalized = 0
                    args['filters'] = attr
                    _self.com_lsm(self, args)

                        
exported_class = BuilderContext
