from zope.interface import Interface, implements
from axiom.store import Store
from axiom.upgrade import registerUpgrader
from axiom.attributes import AND, OR
from axiom import item, attributes, sequence
from epsilon.extime import Time

from urb.util import dlog

import local

filename = u'urb.axiom'

class DataDriver(object):
    def __init__(self, db_name = filename):
        self.db = Store(db_name)

    def close(self):
        # XXX FIXME close the axiom store
        pass

    def commit(self):
        # axiom is autocommit
        pass


    # USER METHODS #
    def new_user(self, nickname, email, adminlevel = 0):
        # First user is always admin
        if len(self.get_all_users()) == 0:
            adminlevel = 100
        u = self.get_user(nickname) 
        if not u:
            dob = Time()
            u = User(store=self.db, nickname=nickname, email=email, dob=dob, adminlevel=adminlevel)
        return u
            
        
    def del_user(self, nickname):
        u = self.get_user(nickname)
        if u:
            u.deleteFromStore()
        
    def get_user(self, nickname):
        r = list(self.db.query(
            User,
            User.nickname == nickname
        ))
        if len(r):
            return r[0]
            
    def get_all_users(self):
        r = list(self.db.query(User))
        return r
        
    def get_character(self, selector):
        r = list(self.db.query(
            CharacterProfile,
            CharacterProfile.selector == unicode(selector)
        ))
        if len(r) == 1:
            return r[0]
            
    # CHARACTER METHODS #
    def new_character(self, selector, fullname):
        c = CharacterProfile(store=self.db, selector=selector, fullname=fullname)
        return c
        
    def del_character(self, selector):
        c = self.get_character(selector)
        if c:
            c.deleteFromStore()
    
    def get_character(self, selector):
        c = list(self.db.query(
            CharacterProfile,
            CharacterProfile.selector==selector
        ))
        if len(c) == 1:
            return c[0]
        
    def get_all_characters(self):
        return list(self.db.query(CharacterProfile))
    
    # MOVE METHODS #
    def new_move(self, selector, fullname, ownerselector):
        m = MoveProfile(store=self.db, selector=selector, fullname=fullname, ownerselector=ownerselector)
        return m
    
    def del_move(self, selector, ownerselector = None):
        m = self.get_move(selector, ownerselector)
        if m:
            m.deleteFromStore()
    
    def get_move(self, selector, ownerselector):
        m = list(self.db.query(
            MoveProfile,
            AND(
                MoveProfile.selector == selector,
                MoveProfile.ownerselector == ownerselector
            )
        ))
        if len(m) == 1:
            return m[0]

    def get_moves_for(self, ownerselector):
        m = list(self.db.query(
            MoveProfile,
            MoveProfile.ownerselector == ownerselector
        ))
        return m
        
    def get_all_moves(self, selector):
        m = list(self.db.query(
            MoveProfile,
            MoveProfile.selector == selector
        ))
        return m
            
    def get_config(self):
        return local

# Service Configuration Items
#class IRCConfig( item.Item ):
#    typeName = 'IRCConfig'
#    schemaVersion = 1

#    network = attributes.text(default = u'irc.freenode.net')
#    port = attributes.text(default = u'6667 8000 8001')
    
#    # dccip = attributes.text(default = u'98.206.16.223')
#    dccip = attributes.text(default = u'98.206.16.223')
#    dccport = attributes.integer(default=8004)
    
#    mainchannel = attributes.text(default = u'#urb')
#    logchannel = attributes.text(default = u'#urb-log')
    
#    channelpass = attributes.text(default = u'mdcclxxvi')
    
    # nickname = attributes.text(default = u'TheHost')
    # nickpass = attributes.text(default = u'mdcclxxvi')

#    nickname = attributes.text(default = u'TheHost')
#    nickpass = attributes.text(default = u'mdcclxxvi')

#class ManholeConfig( item.Item):
#    typeName = 'ManholeConfig'
#    schemaVersion = 1
    
#    network = attributes.text(default = u'irc.freenode.net')
#    port = attributes.text(default = u'6667 8000 6668 8001')
    
#    channel = attributes.text(default = u'#urb')
#    channelpass = attributes.text(default = u'mdcclxxvi')
    
#    nickname = attributes.text(default = u'TheSession')
#    nickpass = attributes.text(default = u'mdcclxxvi')
    
#    timeout = attributes.integer(default = 60)
#    maxlines = attributes.integer(default = 4)

#class WebAdminConfig( item.Item ):
#    typeName = "WebAdminConfig"
#    schemaVersion = 1

#    password = attributes.text(default = u'mdcclxxvi')
#    port = attributes.integer(default = 8001)

# User Account Items
class User( item.Item ):
    typeName = 'User'
    schemaVersion = 1
    
    nickname = attributes.text(indexed=True, allowNone=False)
    dob = attributes.timestamp(allowNone=False)
    email = attributes.text(allowNone=False)
    adminlevel = attributes.integer(default=0)

    wins = attributes.integer(default=0)
    losses = attributes.integer(default=0)
    frags = attributes.integer(default=0)
    deaths = attributes.integer(default=0)
    fatals = attributes.integer(default=0)

    dmgdone = attributes.integer(default=0)
    dmgtaken = attributes.integer(default=0)
    dmghealed = attributes.integer(default=0)
    

class CharacterProfile( item.Item ):
    typeName = 'CharacterProfile'
    schemeVersion = 1

    selector = attributes.text(indexed=True, allowNone=False)
    fullname = attributes.text(allowNone=False)
    description_msg = attributes.text(default=u"")
    selection_msg = attributes.text(default=u"")
    block_begin_msg = attributes.text(default=u"")
    block_fail_msg = attributes.text(default=u"")
    block_success_msg = attributes.text(default=u"")
    rest_msg = attributes.text(default=u"")
    kill_msg = attributes.text(default=u"")
    fatality_msg = attributes.text(default=u"")
    death_msg = attributes.text(default=u"")
    taunt_msg = attributes.text(default=u"")
    
    pstrength = attributes.integer(default=100)
    pdefense = attributes.integer(default=100)
    mstrength = attributes.integer(default=100)
    mdefense = attributes.integer(default=100)

    weakness = attributes.text(default=u"none", allowNone=True)
    resistance = attributes.text(default=u"none", allowNone=True)
    
    # Define validation schema 
    vschema = { 'selector':'str', 'fullname':'msg', 'description_msg':'msg',
        'selection_msg':'msg', 'block_begin_msg':'msg', 'block_fail_msg':'msg',
        'block_success_msg':'msg', 'rest_msg':'msg', 'kill_msg':'msg',
        'fatality_msg':'msg', 'death_msg':'msg', 'taunt_msg':'msg',
        'pstrength':'int', 'pdefense':'int', 'mstrength':'int',
        'mdefense':'int', 'weakness':'str', 'resistance':'str'}
    vorder = ( 'selector', 'fullname', 'resistance', 'weakness',
        'pstrength', 'pdefense', 'mstrength', 'mdefense', 
        'description_msg', 'selection_msg', 'block_begin_msg', 
        'block_fail_msg', 'block_success_msg', 'rest_msg', 'kill_msg',
        'fatality_msg', 'death_msg', 'taunt_msg')
        

class MoveProfile( item.Item ):
    fullname = attributes.text(allowNone=False)
    selector = attributes.text(allowNone=False)
    ownerselector = attributes.text(allowNone=False)
    
    power = attributes.integer(default=100)
    element = attributes.text(default=u"physical", allowNone=True)
    target = attributes.text(default=u"self", allowNone=True)
    # self, ally, ally-all, enemy, enemy-all, all
    cansuper = attributes.integer(default=0)
    cancounter = attributes.integer(default=0)
    effectchances = attributes.text(default=u"")

    prepare_msg = attributes.text(default=u"")
    supr_prepare_msg = attributes.text(default=u"")
    hit_msg = attributes.text(default=u"")
    crit_hit_msg = attributes.text(default=u"")
    supr_hit_msg = attributes.text(default=u"")   

    # Define validation schema
    vschema = {'selector':'str', 'fullname':'msg', 'ownerselector':'str',
        'power':'int', 'element':'str', 'target':'str', 'cansuper':'int',
        'cancounter':'int', 'effectchances':'msg', 'prepare_msg':'msg',
        'supr_prepare_msg':'msg', 'hit_msg':'msg', 'crit_hit_msg':'msg',
        'supr_hit_msg':'msg'}
    vorder = ('selector', 'fullname', 'ownerselector', 'power', 'target',
        'element', 'cansuper', 'cancounter', 'prepare_msg', 'supr_prepare_msg',
        'hit_msg', 'crit_hit_msg', 'supr_hit_msg', 'effectchances') 
