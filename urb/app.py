from twisted.application.service import IService, IServiceCollection
from twisted.python.log import err
from twisted.python.log import msg as log

from urb import db, engine, imports
from urb.event import Signal
from urb.util import dlog

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
        self.database = db.DataDriver()
        
        self.signals['quit'           ] = Signal() # reason
        self.signals['outgoing_msg'   ] = Signal() # destination, message
        self.signals['global_msg'     ] = Signal() # message
        self.signals['game_msg'       ] = Signal() # message
        self.signals['debug_msg'      ] = Signal() # message
        self.signals['login'          ] = Signal() # nickname
        self.signals['logout'         ] = Signal() # nickname
        self.signals['command'        ] = Signal() # player, command, args
        self.signals['signup'         ] = Signal() # player
        self.signals['forfeit'        ] = Signal() # nickname
        self.signals['choose'         ] = Signal() # nickname, selector
        self.signals['ready'          ] = Signal() # nickname
        self.signals['open_selection' ] = Signal() # gametype
        self.signals['close_selection'] = Signal() #
        self.signals['battle_start'   ] = Signal() #
        self.signals['battle_pause'   ] = Signal() #
        self.signals['battle_resume'  ] = Signal() #
        self.signals['battle_abort'   ] = Signal() #
        self.signals['battle_finish'  ] = Signal() # 
        self.signals['battle_queue'   ] = Signal() # command
        self.signals['battle_do'      ] = Signal()
        self.signals['battle_damage'  ] = Signal() # nickname, target, damage

        self.signals['global_msg'].register(self.on_global_msg)
        self.signals['game_msg'].register(self.on_game_msg)
        
        self.game = engine.GameEngine(self)
        self._register_listeners(self.game)
        imports.load_all('commands')
        imports.load_all('gametypes')
        
    def on_game_msg(self, message):
        config = self.database.get_config()
        logchannel = config.irc_log_channel
        to = self.game.fighters.keys()
        to.append(logchannel)
        for recipient in to:
            self.signals['outgoing_msg'].emit(recipient, message)
            
    def on_global_msg(self, message):
        config = self.database.get_config()
        logchannel = config.irc_log_channel
        mainchannel = config.irc_main_channel
        to = self.game.players.keys()
        to.append(logchannel)
        to.append(mainchannel)
        for recipient in to:
            self.signals['outgoing_msg'].emit(recipient, message)
                    
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
            
    def tell(self, player, message):
        return self.signals['outgoing_msg'].emit(player.nickname, message)

    def do_command(self, nickname, command, args):
        if nickname in self.game.players:
            self.signals['command'].emit(self.game.players[nickname], command, args)
            self.database.commit()
    
