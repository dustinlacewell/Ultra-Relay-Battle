from urb.util import dlog

import local
import datetime

from ZODB import FileStorage, DB
from BTrees.OOBTree import OOBTree
from persistent import Persistent
import transaction

filename = u'urb.zodb'

_storage = FileStorage.FileStorage(filename)
_db = DB(_storage)
_connection = _db.open()
root = _connection.root()

def deploy_schema():
    # ensure the db is up to date.  Creating these keys is
    # effectively a schema version 0->1 migration, which we should
    # formalize at some point, but we'll hardwire it for now.
    for key in "Users Moves Characters GameSettings".split():
        if key not in root:
            root[key] = OOBTree()
        else:
            for object in root[key].values():
                if key == 'GameSettings':
                    gs = GameSettings()
                    for attr in GameSettings.vorder:
                        if not hasattr(object, attr):
                            val = getattr(gs, attr)
                            setattr(object, attr, val)
                elif key == 'Characters':
                    cp = CharacterProfile(object.selector, object.fullname)
                    for attr in CharacterProfile.vorder:
                        if not hasattr(object, attr):
                            val = getattr(cp, attr)
                            setattr(object, attr, val)
                elif key == 'Moves':
                    mp = MoveProfile(object.selector, object.fullname, object.ownerselector)
                    for attr in MoveProfile.vorder:
                        if not hasattr(object, attr):
                            val = getattr(mp, attr)
                            setattr(object, attr, val)
                    for attr in ['_info_str', 'info']:
                        if not hasattr(object, attr):
                            val = getattr(MoveProfile, attr)
                            setattr(object, attr, val)
            
    

def commit():
    transaction.commit()

def close():
    # XXX nothing uses this, so we have to rely on the default shutdown behavior for now
    _connection.close()
    _db.close()
    _storage.close()

def get_config():
    return local

class DatabaseBaseException(Exception):
       def __init__(self, value):
           self.parameter = value
       def __str__(self):
           return repr(self.parameter)
       
class DBGetException(DatabaseBaseException):
    pass


class User( Persistent ):
    def __init__(self, nickname, email, dob, adminlevel):
        self.nickname = nickname
        self.email = email
        self.dob = dob
        self.adminlevel = adminlevel

        self.wins   = 0
        self.losses = 0
        self.frags  = 0
        self.deaths = 0
        self.fatals = 0

        self.dmgdone   = 0
        self.dmgtaken  = 0
        self.dmghealed = 0
        
    @classmethod
    def all(cls):
        return root['Users'].values()
        
    @classmethod
    def create(cls, nickname, email, adminlevel=0):
        if len(cls.all()) == 0:
            adminlevel = 100
        dob = datetime.datetime.now()
        newuser = cls(nickname, email, dob, adminlevel)
        root['Users'][nickname] = newuser
        commit()
        
    @classmethod
    def get(cls, **kwargs):
        all = cls.all()
        matched = []
        for item in all:
            missing = [attr for attr in kwargs if not hasattr(item, attr)]
            if missing:
                raise DBGetException("The following attributes are invalid: %s" % missing)
            else:
                invalid = [attr for attr, val in kwargs.iteritems() if getattr(item, attr) != val]
                if len(invalid) == 0:
                    matched.append(item)
        if len(matched) > 1:
            raise DBGetException("The get request returned multiple objects!")
        else:
            return matched[0]
        
    @classmethod
    def filter(cls, **kwargs):
        all = cls.all()
        matched = []
        for item in all:
            missing = [attr for attr in kwargs if not hasattr(item, attr)]
            if missing:
                raise DBGetException("The following attributes are invalid: %s" % missing)
            else:
                invalid = [attr for attr, val in kwargs.iteritems() if getattr(item, attr) != val]
                if len(invalid) == 0:
                    matched.append(item)
        return matched
    
    def delete(self):
        del root['Users'][self.nickname]
        commit()

class CharacterProfile( Persistent ):
    def __init__(self, selector, fullname):
        self.selector = selector
        self.fullname = fullname

        self.description_msg   = u''
        self.selection_msg     = u''
        self.block_begin_msg   = u''
        self.block_fail_msg    = u''
        self.block_success_msg = u''
        self.rest_msg          = u''
        self.kill_msg          = u''
        self.fatality_msg      = u''
        self.death_msg         = u''
        self.taunt_msg         = u''

        self.pstrength         = 50
        self.pdefense          = 50
        self.mstrength         = 50
        self.mdefense          = 50

        self.weakness          = u'none'
        self.resistance        = u'none'
        
        self.finalized         = 0
        
    def get_gauge(self, attribute):
        val = getattr(self, attribute)
        bar = "*" * int(val / 10.0)
        filler = " " * (10 - len(bar))
        return "[%s%s]" % (bar, filler)

    vschema = { 'selector':'str', 'fullname':'msg', 'description_msg':'msg',
        'selection_msg':'msg', 'block_begin_msg':'msg', 'block_fail_msg':'msg',
        'block_success_msg':'msg', 'rest_msg':'msg', 'kill_msg':'msg',
        'fatality_msg':'msg', 'death_msg':'msg', 'taunt_msg':'msg',
        'pstrength':'int', 'pdefense':'int', 'mstrength':'int',
        'mdefense':'int', 'weakness':'str', 'resistance':'str', 'finalized':'int'}

    vorder = ( 'selector', 'fullname', 'resistance', 'weakness',
        'pstrength', 'pdefense', 'mstrength', 'mdefense', 
        'description_msg', 'selection_msg', 'block_begin_msg', 
        'block_fail_msg', 'block_success_msg', 'rest_msg', 'kill_msg',
        'fatality_msg', 'death_msg', 'taunt_msg', 'finalized')

# CHARACTER METHODS #
def new_character(selector, fullname):
    c = CharacterProfile(selector=selector, fullname=fullname)
    root['Characters'][selector] = c
    return c

def get_character(selector):
    return root['Characters'].get(selector)
    
def del_character(selector):
    del root['Characters'][selector]

def get_all_characters():
    return root['Characters'].values()

def change_character_selector(oldselector, newselector):
    c = get_character(oldselector)
    root['Characters'][newselector] = c
    del_character(oldselector)
    print oldselector, newselector
    print list(root['Characters'])

class MoveProfile( Persistent ):
    def __init__(self, selector, fullname, ownerselector):
        self.selector      = selector
        self.fullname      = fullname
        self.ownerselector = ownerselector

        self.power   = 100
        self.element = u"physical"
        self.target  = u"enemy"

        self.cansuper      = 0
        self.cancounter    = 0
        self.effectchances = u''

        self.prepare_msg      = u''
        self.supr_prepare_msg = u''
        self.hit_msg          = u''
        self.miss_msg         = u''
        self.crit_hit_msg     = u''
        self.supr_hit_msg     = u''   
        
    def _info_str(self):
        return "(%s) %s : %d : %s : %s : %s %s" % (
                self.selector, self.fullname, self.power, self.element, self.target,
                "CanSpr+" if self.cansuper else "",
                "CanCtr+" if self.cancounter else "",
                )
    info = property(_info_str)


    vschema = {'selector':'str', 'fullname':'msg', 'ownerselector':'str',
        'power':'int', 'element':'element', 'target':'str', 'cansuper':'int',
        'cancounter':'int', 'effectchances':'msg', 'prepare_msg':'msg',
        'supr_prepare_msg':'msg', 'hit_msg':'msg', 'miss_msg':'msg',
        'crit_hit_msg':'msg', 'supr_hit_msg':'msg'}

    vorder = ('selector', 'fullname', 'ownerselector', 'power', 'target',
        'element', 'cansuper', 'cancounter', 'prepare_msg', 'supr_prepare_msg',
        'hit_msg', 'miss_msg', 'crit_hit_msg', 'supr_hit_msg', 'effectchances') 


# MOVE METHODS
# moves belong to characters, so most of these DAO methods are invisible when we have full OO/ORM
def new_move(selector, fullname, ownerselector):
    m = MoveProfile(selector=selector, fullname=fullname, ownerselector=ownerselector)
    root['Moves'][(selector,ownerselector)] = m
    return m

def del_move(selector, ownerselector = None):
    del root['Moves'][(selector, ownerselector)]

def get_move(selector, ownerselector):
    return root['Moves'].get((selector,ownerselector))
    # return first move matching selector and ownerselector
    pass

def get_moves_for(ownerselector):
    # XXX HACK even an OODB query doesn't have to be this stupid,
    # this is just quick and dirty querying
    return [m for m in root['Moves'].values() if m.ownerselector == ownerselector]
    
def get_all_moves(selector):
    return [m for m in root['Moves'].values() if m.selector == selector]

def change_move_selector(ownerselector, oldselector, newselector):
    m = get_move(oldselector, ownerselector)
    root['Moves'][(newselector, ownerselector)] = m
    del_move(ownerselector, oldselector)
    
class GameSettings( Persistent ):
    def __init__(self):
        self.starthealth = 600
        self.startmagic = 600
        self.startsuper = 0
        self.maxhealth = 1000
        self.maxmagic = 600
        self.maxsuper = 600
        self.maxsuperlevel = 6
        self.damagemultiplier = 1.0
        self.mprate = 3
        
    vschema = {'starthealth':'int', 'startmagic':'int', 'startsuper':'int',
               'maxhealth':'int', 'maxmagic':'int', 'maxsuper':'int',
               'maxsuperlevel':'int', 'damagemultiplier':'float', 'mprate':'int',
    }
    vorder = ('starthealth', 'startmagic', 'startsuper',
              'maxhealth', 'maxmagic', 'maxsuper', 'maxsuperlevel',
              'damagemultiplier', 'mprate')
    
def get_gametype(name):
    gtype = root['GameSettings'].get(name)
    if gtype:
        return gtype
    root['GameSettings'][name] = GameSettings()
    return get_gametype(name)        

deploy_schema()