from textwrap import wrap

from django.conf import settings
from django.contrib.auth import models, authenticate

from urb import contexts, commands, validation
from urb.players.models import Player
from urb.constants import MOTD 
from urb.util import dlog, dtrace

class SessionManager(dict):
    def __init__(self, app):
        dict.__init__(self)
        self.app = app

    def register(self, username, password, email):
        player = models.Player(
            username=username,
            email=email
        )
        player.set_password(password)
        player.save()
        return player

    def get_players(self):
        return Player.objects.filter(id__in=self.sessions.keys())
    players = property(get_players)

    def msg(self, pid, message, **kwargs):
        if id in self:
            self[pid].msg(message, **kwargs)

    def login(self, username, password, client):
        player = authenticate(username=username, password=password)

        if player is None:
            return

        session = self.get(
            player.id, 
            Session(self.app, player.id, client)
        )

        session.client = client

        player_count = len(self)
        motd = MOTD % (player.username, player_count)
        for wline in motd.splitlines():
            if wline.strip():
                for line in wrap(wline, player.linewidth, drop_whitespace=False):
                    session.msg(line, fmt=" ^")
            else:
                session.msg(wline)
        session.switch('mainmenu') 
        return session
        
    def logout(self, pid):
        # if self.game and nickname in self.game.fighters:
        #     self.game.player_forfeit(nickname)
        if pid in self:
            del self[nickname]


class Session(object):
    """
    Session
    
    The session manages a player's context and the ability
    to switch between them.
    """
    def __init__(self, app, pid, client):
        self.app = app
        self.pid = pid
        self.client = client
        self.context = None
        self.context_name = None
        
    def switch(self, context):
        ctxcls = contexts.get(context)
        if ctxcls:
            if self.context:
                self.context.leave(self)
            self.context_name = context   
            self.context = ctxcls(self)
            self.context.enter(self)

    def get_player(self):
        return Player.objects.get(id=self.pid)
    player = property(get_player)

    def revert(self):
        self.switch('mainmenu')

    def msg(self, message, fmt=" <"):
        if message.strip():
            wrapped = wrap(
                message, 80,
                drop_whitespace=False, 
                replace_whitespace=False
            )
            for line in wrapped:
                line = "- {0:{fmt}{mlw}}".format(
                    line, 
                    fmt=fmt, 
                    mlw=80,
                )                    
                self.client.msg(line)
        else:
            message = "- {0:{fmt}{mlw}}".format(
                message, 
                fmt=fmt, 
                mlw=80,
            )
            self.msg(message)

    def cmd(self, command, args):
        player = self.get_player()

        # inter-context commands
        if '.' in command:
            parts = command.split('.')
            if len(parts) != 2:
                self.msg("Inter-context commands take the form: context.command arg1 ... argN")
                return
            context_name, command = parts
            if context_name not in ['build', 'admin']:
                self.msg("Context must be one of: build, admin")
                return
            context_name = {'build':'builder', 'admin':'administration'}[context_name] # convert to true name
            ctxcls = contexts.get(context_name)
            if not ctxcls:
                self.msg("The %s context could not be loaded remotely." % context_name)
                return
            contextual = "com_%s" % command
            if not hasattr(ctxcls, contextual) or contextual == "com_exit":
                self.msg("The %s context has no %s command." % (context_name, command))
                return
            context = ctxcls(self)
            contextual = getattr(context, contextual)
            # run validation
            try:
                data = validation.command(self, contextual, args)
                # run if valid
                contextual(self, data)
                # db.commit()
                return
            except validation.ValidationError, e:
                self.msg(e.message)
                return
            except Exception, e:
                self.msg("Sorry, that command resulted in an error on the server.")
                return    

        # Let context handle input if it wants
        if self.context.on_input(self, command, args):
            # db.commit()
            return
        # determine the usable commands for this player
        clocals, cglobals = commands.get_allowed(self)
        if command in clocals+cglobals: # only respond to allowed commands
            # format for context based commands
            contextual = "com_%s" % command
            # session contextual command
            if hasattr(self.context, contextual):
                # get the command
                contextual = getattr(self.context, contextual)
                # validate passed arguments against schema
                try: 
                    data = validation.command(self.app, contextual, args)
                    # run the comand if validated
                    contextual(self, data)
                except validation.ValidationError, e:
                    self.msg(e.message)
                except Exception, e:
                      self.msg("Sorry, that command resulted in an error on the server.")                      
                      dtrace("Context command caused an error : %s %s" % (command, args))
            else: # its not contextual so check dynamic commands
                comm_cls = commands.get(command)
                if comm_cls:
                    # validate passed arguments against schema
                    try: 
                        data = validation.command(self.app, comm_cls, args)
                        # create live command object
                        new_comm = comm_cls(self, data)
                        # let command verify submission
                        new_comm.verify()
                        new_comm.perform()
                        return
                    except validation.ValidationError, e:
                        self.msg(e.message)
                    except Exception, e:
                        self.msg("Sorry, that command resulted in an error on the server.")
                        dtrace("Dynamic command caused an error : %s %s" % (command, args))
                else: # Inform the player the command isn't available
                    self.msg("'%s' isn't an available command." % command)
        else: # Inform the player the command isn't available
            self.msg("'%s' isn't an available command." % command)

