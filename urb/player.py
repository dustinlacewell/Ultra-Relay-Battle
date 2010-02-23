from urb import contexts
from urb.util import dlog
          

class Player(object):
    """
    Player
    
    The Player class represents a user account who is logged in.
    It maintains everything associated with the player game
    related or not. This includes any game related attributes
    but also the user's command session.
    """
    
    def __init__(self, nickname, session, app):
        self.nickname = nickname
        self.app = app
        self.db = app.database
        self.session = session        
        self.user = self.db.get_user(nickname)
        
        self.team = 0
        
        self.character = None
        self.current_move = None
        self.ready = False
        self.health = 0
        self.superpoints = 0
        self.magicpoints = 0
        
    def _status_msg(self):
        """Generate in-game status message"""
        action = "READY"
        if self.current_move:
            if self.current_move.target:
                action = "doing '%s' on %s" % (self.current_move.name, self.current_move.target)
            else:
                action = "doing '%s'" % (self.current_move.name)
        return "%s is %s : %dHP : %dMP : %dSP" % (self.nickname, action, self.health, self.magicpoints, self.superpoints)
    status_msg = property(_status_msg)
    
    def _get_ready(self):
        """Return a boolean whether play is ready."""
        return self.current_move == None
    
    def halt(self):
        if self.ready:
            self.app.tell(self.nickname, "You're not doing anything yet!")
        else:
            self.app.signals['game_msg'].emit("%s stops doing '%s'." % (self.nickname, self.current_move.name))
            theplayer.ready = True
            theplayer.current_move = None
            self.app.signals['game_msg'].emit(theplayer.status_msg)
    
    ready = property(_ready)   

class Session(object):
    """
    Session
    
    The session manages a player's context and the ability
    to switch between them.
    
    TODO: Update to maintain session after disconnect.
    """
    def __init__(self, nickname, app):
        self.nickname = nickname
        self.app = app
        self.context = None
        self.context_name = None
        self.last_context_name = None
                        
    def switch(self, context):
        ctxcls = contexts.get(context)
        if ctxcls:
            if self.context:
                self.last_context_name = self.context_name
                self.context.leave(self)
            self.context_name = context   
            self.context = ctxcls(self)
            self.context.enter(self)
            
    def revert(self):
        if self.last_context_name:
            self.switch(self.last_context_name)
