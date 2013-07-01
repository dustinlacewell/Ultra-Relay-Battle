from twisted.application.service import IService, IServiceCollection
from twisted.python.log import err
from twisted.python.log import msg as log

from urb.constants import MOTD, MLW
from urb import imports, commands, validation
from urb.event import Signal
from urb.players.models import Player
from urb.util import dlog, dtrace
from urb import contexts
from urb.gametypes.manager import GameManager
from urb.contexts.session import SessionManager

class ApplicationClass(object):
    '''The root namespace object for URB, holding references to
    application-level singletons including the persistence database,
    game engine, all globally defined named events ('signals').

    Front-ends the Twisted service infrastructure, augmenting the
    standard service lifecycle with event registration and hookup.

    Additionally defines some convenience methods for global event
    origination (currently just .tell() for broadcasting text)
    '''

    signals = {}
    
    def __init__(self):
        # Service References #
        self._services = {}
        
        self.sessions = SessionManager(self)
        self.games = GameManager(self)
        
        imports.load_all('commands')
        imports.load_all('gametypes')

    # def _get_lobbyists(self):
    #     if self.game == None:
    #         return self.players
    #     else:
    #         lobbyists = {}
    #         for nickname, player in self.players.iteritems():
    #             if nickname not in self.game.fighters:
    #                 lobbyists[nickname] = player
    #         return lobbyists
    # lobbyists = property(_get_lobbyists)

    def session_for(self, pid):
        return self.sessions.get(pid, None)

    def msg(self, pid, message, **kwargs):
        self.sessions.msg(pid, message, **kwargs)
    tell = msg            

    def global_msg(self, message, **kwargs):
        for pid, session in self.sessions:
            session.msg(message, **kwargs)
            
    # def set_game(self, gametype):
    #     self.game = gametype(self)
    #     self.game.open_selection()
        
    # def unset_game(self):
    #     if self.game:
    #         self.game.abort_battle()
    #         self.game = None
                    
    def _register_listeners(self, service):
        '''
        Registers all event handlers for a service.
        '''
        signalmatrix = service.get_signal_matrix()
        for signal, handler in signalmatrix.items():
            try:
                #Register the service's  handler to the event system's signal
                self.signals[signal].register(handler)
            except KeyError:
                log("couldnt find a '%s' signal for registration" % signal)
              
    def _unregister_listeners(self, service):
        '''
        Unregisters all event handlers for a service.
        '''
        signalmatrix = service.get_signal_matrix()
        for signal, handler in signalmatrix.items():
            try:
                self.signals[signal].unregister(handler)
            except KeyError:
                log("couln't find a '%s' signal to unregister" % signal)
                
    def add_service(self, svc_class):
        name = svc_class.service_name
        log("Starting %s" % name)
        service = svc_class(self)
        self._register_listeners(service)
        log("%s started." % name)
        service.setServiceParent(self.application)
        self._services[name] = service

    def inject_service(self, svc_inst, svc_name):
        log("Injecting %s" % svc_name)
        self._register_listeners(svc_inst)
        svc_inst.setServiceParent(self.application)
        self._services[name] = svc_inst
        log("%s injected." % svc_name)
        
    def start_service(self, name):
        svc = self.application.getServiceName(name)
        svc.startService()
        svc.register_listeners(svc)
        
    def stop_service(self, name):
        svc = self.application.getServiceNamed(name)
        svc.stopService()
        svc._unregister_listeners(svc)
        
    def get_service(self, name):
        try: 
            svc = IServiceCollection(self.application).getServiceNamed(name)
        except KeyError:
            svc = None
        return svc
        
    def is_svc_running(self, name):
        svc = self.get_service(name)
        if svc:
            return IService(svc.running)
    
    # def lsay(self, message, fmt=" <", channel=True):
    #     config = db.get_config()
    #     mainchannel = config.irc_main_channel
    #     for nick, player in self.lobbyists.iteritems():
    #         player.tell(message, fmt)
    #     if channel:
    #         for line in wrap(message, MLW, drop_whitespace=False, replace_whitespace=False):
    #             self.signals['outgoing_msg'].emit(mainchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
    

    # def fsay(self, message, fmt=" <", channel=True):
    #     config = db.get_config()
    #     logchannel = config.irc_log_channel
    #     if self.game:
    #         for nick, player in self.game.fighters.iteritems():
    #             player.tell(message, fmt)
    #         if channel:
    #             for line in wrap(message, MLW, drop_whitespace=False, replace_whitespace=False):
    #                 self.signals['outgoing_msg'].emit(logchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
            
    # def gsay(self, message, fmt=" <", channel=True):
    #     config = db.get_config()
    #     logchannel = config.irc_log_channel
    #     mainchannel = config.irc_main_channel
    #     for nick, player in self.players.iteritems():
    #         player.tell(message, fmt)
    #     if channel:
    #         for line in wrap(message, MLW, drop_whitespace=False, replace_whitespace=False):
    #             self.signals['outgoing_msg'].emit(logchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
    #             self.signals['outgoing_msg'].emit(mainchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
        
