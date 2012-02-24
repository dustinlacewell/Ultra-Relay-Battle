from textwrap import wrap

from twisted.application.service import IService, IServiceCollection
from twisted.python.log import err
from twisted.python.log import msg as log

from urb.constants import MOTD, MLW
from urb import db, imports, commands, validation
from urb.event import Signal
from urb.player import Player, Session
from urb.util import dlog, dtrace
from urb import contexts
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
        
        self.signals['quit'           ] = Signal() # reason
        self.signals['outgoing_msg'   ] = Signal() # destination, message
        self.signals['global_msg'     ] = Signal() # message
        self.signals['debug_msg'      ] = Signal() # message
        self.signals['login'          ] = Signal() # nickname
        self.signals['logout'         ] = Signal() # nickname

        self.signals['global_msg'].register(self.on_global_msg)
        self.signals['login'].register(self.on_login)
        self.signals['logout'].register(self.on_logout)
        
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
            
    def on_global_msg(self, message):
        config = db.get_config()
        # logchannel = config.irc_log_channel
        # mainchannel = config.irc_main_channel
        # to = self.game.players.keys()
        # to.append(logchannel)
        # to.append(mainchannel)
        for recipient in self.sessions.usernames:
            self.signals['outgoing_msg'].emit(recipient, message)
            
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
            
    def tell(self, player, message, fmt=" <"):
        username = player.user.username
        if message.strip():
            wrapped = wrap(message, player.linewidth, 
                           drop_whitespace=False, replace_whitespace=False)
            for line in wrapped:
                self.signals['outgoing_msg'].emit(username, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=player.linewidth))
        else:
            self.signals['outgoing_msg'].emit(username, "- {0:{fmt}{mlw}}".format(message, fmt=fmt, mlw=player.linewidth))
    
    def lsay(self, message, fmt=" <", channel=True):
        config = db.get_config()
        mainchannel = config.irc_main_channel
        for nick, player in self.lobbyists.iteritems():
            player.tell(message, fmt)
        if channel:
            for line in wrap(message, MLW, drop_whitespace=False, replace_whitespace=False):
                self.signals['outgoing_msg'].emit(mainchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
    

    def fsay(self, message, fmt=" <", channel=True):
        config = db.get_config()
        logchannel = config.irc_log_channel
        if self.game:
            for nick, player in self.game.fighters.iteritems():
                player.tell(message, fmt)
            if channel:
                for line in wrap(message, MLW, drop_whitespace=False, replace_whitespace=False):
                    self.signals['outgoing_msg'].emit(logchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
            
    def gsay(self, message, fmt=" <", channel=True):
        config = db.get_config()
        logchannel = config.irc_log_channel
        mainchannel = config.irc_main_channel
        for nick, player in self.players.iteritems():
            player.tell(message, fmt)
        if channel:
            for line in wrap(message, MLW, drop_whitespace=False, replace_whitespace=False):
                self.signals['outgoing_msg'].emit(logchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
                self.signals['outgoing_msg'].emit(mainchannel, "- {0:{fmt}{mlw}}".format(line, fmt=fmt, mlw=MLW))
        
    def do_command(self, nickname, command, args):
        player = self.players[nickname]
        # inter-context commands
        if '.' in command:
            parts = command.split('.')
            if len(parts) != 2:
                player.tell("Inter-context commands take the form: context.command arg1 ... argN")
                return
            context_name, command = parts
            if context_name not in ['build', 'admin']:
                player.tell("Context must be one of: build, admin")
                return
            context_name = {'build':'builder', 'admin':'administration'}[context_name] # convert to true name
            ctxcls = contexts.get(context_name)
            if not ctxcls:
                player.tell("The %s context could not be loaded remotely." % context_name)
                return
            contextual = "com_%s" % command
            if not hasattr(ctxcls, contextual) or contextual == "com_exit":
                player.tell("The %s context has no %s command." % (context_name, command))
                return
            context = ctxcls(self)
            contextual = getattr(context, contextual)
            # run validation
            try:
                data = validation.command(self, contextual, args)
                # run if valid
                contextual(player.session, data)
                db.commit()
                return
            except validation.ValidationError, e:
                self.tell(player, e.message)
                return
            except Exception, e:
                self.tell(player, "Sorry, that command resulted in an error on the server.")
                return    

        # Let context handle input if it wants
        if player.session.context.on_input(player.session, command, args):
            db.commit()
            return
        # determine the usable commands for this player
        clocals, cglobals = commands.get_allowed(player)
        if command in clocals+cglobals: # only respond to allowed commands
            # format for context based commands
            contextual = "com_%s" % command
            # session contextual command
            if hasattr(player.session.context, contextual):
                # get the command
                contextual = getattr(player.session.context, contextual)
                # validate passed arguments against schema
                try: 
                    data = validation.command(self, contextual, args)
                    # run the comand if validated
                    contextual(player.session, data)
                    db.commit()
                except validation.ValidationError, e:
                    self.tell(player, e.message)
                except Exception, e:
                      self.tell(player, 
                      "Sorry, that command resulted in an error on the server.")                      
                      dtrace("Context command caused an error : %s %s" % (command, args))
            else: # its not contextual so check dynamic commands
                comm_cls = commands.get(command)
                if comm_cls:
                    # validate passed arguments against schema
                    try: 
                        data = validation.command(self, comm_cls, args)
                        # create live command object
                        new_comm = comm_cls(self, player, data)
                        # let command verify submission
                        new_comm.verify()
                        new_comm.perform()
                        db.commit()
                        return
                    except validation.ValidationError, e:
                        self.tell(player, e.message)
                    except Exception, e:
                        self.tell(player, 
                        "Sorry, that command resulted in an error on the server.")
                        dtrace("Dynamic command caused an error : %s %s" % (command, args))
                else: # Inform the user the command isn't available
                    self.tell(player, "'%s' isn't an available command." % command)
        else: # Inform the user the command isn't available
            self.tell(player, "'%s' isn't an available command." % command)
            
    def on_login(self, nickname):
        # Create the player object with the session
        newplayer = Player(nickname, self)
        session = Session(newplayer, self)
        newplayer.session = session
        if nickname in self.players:
            oldsession = self.players[nickname].session
            newplayer.session = oldsession
            self.players[nickname] = newplayer
            if self.game and nickname in self.game.fighters:
                self.game.fighters[nickname] = newplayer
        else:
            self.players[nickname] = newplayer
        player_count = len(self.players) - 1
        motd = MOTD % (nickname, player_count)
        for wline in motd.splitlines():
            if wline.strip():
                for line in wrap(wline, newplayer.linewidth, drop_whitespace=False):
                    self.tell(newplayer, line, fmt=" ^")
            else:
                self.tell(newplayer, wline)
        session.switch('mainmenu') 
        
    def on_logout(self, nickname):
        if self.game and nickname in self.game.fighters:
            self.game.player_forfeit(nickname)
        if nickname in self.players:
            del self.players[nickname]
    
