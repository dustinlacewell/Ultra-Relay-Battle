from urb.util import dlog

import local
import datetime

from ZODB import FileStorage, DB
from BTrees.OOBTree import OOBTree
from persistent import Persistent
import transaction

filename = u'urb.zodb'

class DataDriver(object):
    def __init__(self, db_name = filename):
        self.storage = FileStorage.FileStorage(db_name)
        self.db = DB(self.storage)
        self.connection = self.db.open()
        self.dbroot = self.connection.root()
        self.deploy_schema()

    def deploy_schema(self):
        # ensure the db is up to date.  Creating these keys is
        # effectively a schema version 0->1 migration, which we should
        # formalize at some point, but we'll hardwire it for now.
        root = self.dbroot
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
                
        

    def commit(self):
        transaction.commit()

    def close(self):
        # XXX nothing uses this, so we have to rely on the default shutdown behavior for now
        self.connection.close()
        self.db.close()
        self.storage.close()

    def get_config(self):
        return local

    # USER METHODS #
    def new_user(self, nickname, email, adminlevel = 0):
        # First user is always admin
        if len(self.get_all_users()) == 0:
            adminlevel = 100
        u = self.get_user(nickname) 
        if not u:
            dob = datetime.datetime.now()
            u = User(nickname=nickname, email=email, dob=dob, adminlevel=adminlevel)
            self.dbroot['Users'][nickname] = u
        return u
        
    def del_user(self, nickname):
        del self.dbroot['Users'][nickname]
        
    def get_user(self, nickname):
        return self.dbroot['Users'].get(nickname)
            
    def get_all_users(self):
        return self.dbroot['Users'].values()

    # CHARACTER METHODS #
    def new_character(self, selector, fullname):
        c = CharacterProfile(selector=selector, fullname=fullname)
        self.dbroot['Characters'][selector] = c
        return c

    def get_character(self, selector):
        return self.dbroot['Characters'].get(selector)
        
    def del_character(self, selector):
        del self.dbroot['Characters'][selector]

    def get_all_characters(self):
        return self.dbroot['Characters'].values()
    
    def change_character_selector(self, oldselector, newselector):
        c = self.get_character(oldselector)
        self.dbroot['Characters'][newselector] = c
        self.del_character(oldselector)
        print oldselector, newselector
        print list(self.dbroot['Characters'])
    
    
    # MOVE METHODS
    # moves belong to characters, so most of these DAO methods are invisible when we have full OO/ORM
    def new_move(self, selector, fullname, ownerselector):
        m = MoveProfile(selector=selector, fullname=fullname, ownerselector=ownerselector)
        self.dbroot['Moves'][(selector,ownerselector)] = m
        return m
    
    def del_move(self, selector, ownerselector = None):
        del self.dbroot['Moves'][(selector, ownerselector)]
    
    def get_move(self, selector, ownerselector):
        return self.dbroot['Moves'].get((selector,ownerselector))
        # return first move matching selector and ownerselector
        pass

    def get_moves_for(self, ownerselector):
        # XXX HACK even an OODB query doesn't have to be this stupid,
        # this is just quick and dirty querying
        return [m for m in self.dbroot['Moves'].values() if m.ownerselector == ownerselector]
        
    def get_all_moves(self, selector):
        return self.dbroot['Moves'].values()
    
    def change_move_selector(self, ownerselector, oldselector, newselector):
        m = get_move(oldselector, ownerselector)
        self.dbroot['Moves'][(newselector, ownerselector)] = m
        self.del_move(ownerselector, oldselector)
        
    def get_gametype(self, name):
        gtype = self.dbroot['GameSettings'].get(name)
        if gtype:
            return gtype
        self.dbroot['GameSettings'][name] = GameSettings()
        return self.get_gametype(name)
        

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
        self.crit_hit_msg     = u''
        self.supr_hit_msg     = u''   


    vschema = {'selector':'str', 'fullname':'msg', 'ownerselector':'str',
        'power':'int', 'element':'element', 'target':'str', 'cansuper':'int',
        'cancounter':'int', 'effectchances':'msg', 'prepare_msg':'msg',
        'supr_prepare_msg':'msg', 'hit_msg':'msg', 'crit_hit_msg':'msg',
        'supr_hit_msg':'msg'}

    vorder = ('selector', 'fullname', 'ownerselector', 'power', 'target',
        'element', 'cansuper', 'cancounter', 'prepare_msg', 'supr_prepare_msg',
        'hit_msg', 'crit_hit_msg', 'supr_hit_msg', 'effectchances') 

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