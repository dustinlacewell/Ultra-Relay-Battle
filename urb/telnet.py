import os, chardet, struct, collections
from collections import deque
import traceback

from twisted.application import internet
from twisted.conch.telnet import TelnetTransport, TelnetProtocol, TelnetBootstrapProtocol
from twisted.conch.insults.helper import TerminalBuffer
from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.recvline import HistoricRecvLine
from twisted.internet import protocol
from twisted.protocols import basic
from twisted.internet.protocol import ServerFactory

# environment setup for Django project files
os.environ['DJANGO_SETTINGS_MODULE'] = 'urb.web.settings'
from django.conf import settings

from urb.db import *
from urb import app
from urb.util import dlog
from urb.commands import get_allowed, get
from urb import validation as v
from urb.constants import MLW
from urb import contexts
from urb.validation import ValidationError

class TelnetProtocol(HistoricRecvLine):

    delimiter = '\n'
    ps = ['> ']        

    def __init__(self, app):
        self.app = app
        self.handler = self.on_lobby_command
        self.nickname = None
        self.display_history = deque()
        self.tabchoices = []
        self.tabarg = None
        self.drawInput = False
        HistoricRecvLine.__init__(self)
        
    def _get_prompt(self):
        return self.ps[self.pn]
    prompt = property(_get_prompt)
    
    def _get_status(self):
        if self.nickname and self.nickname in self.app.players:
            player = self.app.players[self.nickname]
            if isinstance(player.session.context,  contexts.get('battle')):
                ready = player.current_move.name.capitalize() if player.current_move else "READY"
                status = "# {p.health}HP:{p.magicpoints}MP:{p.superpoints}SP #-{ready}".format(p=player, ready=ready)
                result = status + "{0:-^{1}}".format('-', MLW - len(status))
                return result
            else:
                return "{0:-^{1}}".format("Ultra Relay Battle 0.9", MLW + 2) # +2 for no prompt
        else:
            return "{0:-^{1}}".format("Ultra Relay Battle 0.9", MLW + 2)
    status = property(_get_status)
    
    def initializeScreen(self):
        self.terminal.reset()
        self.setInsertMode()
        for x in xrange(256): self.sendLine("\n")
        self.sendLine("Ultra Relay Battle - conch interface :")
        self.sendLine("   create <username> <email> <password>")
        self.sendLine("   connect <username> <password>")
        self.drawInputLine()
    
    def reset_tab(self):
        self.tabchoices = []
        self.tabarg = None

    def characterReceived(self, ch, moreCharactersComing):
        self.reset_tab()
        HistoricRecvLine.characterReceived(self, ch, moreCharactersComing)
        
    def handle_BACKSPACE(self):
        self.reset_tab()
        HistoricRecvLine.handle_BACKSPACE(self)
        
    def handle_RETURN(self):
        self.reset_tab()
        if self.lineBuffer: # prevent empty submission
            self.sendLine(" ")
            return HistoricRecvLine.handle_RETURN(self)
        
    def handle_TAB(self):
        if self.nickname: # only tab once logged in
            parts = ''.join(self.lineBuffer).split(' ')
            player = self.app.players[self.nickname]
            comname = parts[0]
            
            if self.tabchoices and self.tabarg != None: # if queue, cycle
                self.tabchoices.append( self.tabchoices.pop(0) )
                choice = self.tabchoices[0]
                
                end = len(self.lineBuffer)
                diff = end - self.lineBufferIndex
                
                for x in xrange(diff):
                    self.handle_RIGHT()
                for x in range(end):
                    HistoricRecvLine.handle_BACKSPACE(self)
                    
                parts[self.tabarg] = choice
                newline = ' '.join(parts)
                end = len(' '.join(parts[:self.tabarg + 1]))
                 
                for c in newline:
                    HistoricRecvLine.characterReceived(self, c, None)
                
                diff = abs(end - self.lineBufferIndex)
                
                for x in xrange(diff):
                    self.handle_LEFT()
                    
            else: # determine tabchoices
                # complete commands
                if len(parts) == 1:
                    if '.' in parts[0]:
                        _parts = parts[0].split('.')
                        if len(_parts) != 2:
                            player.tell("Inter-context commands take the form: context.command arg1 ... argN")
                            return
                        context_name, command = _parts
                        if context_name not in ['build', 'admin'] and command != 'exit':
                            player.tell("Context must be one of: build, admin")
                            return
                        _context_name = {'build':'builder', 'admin':'administration'}[context_name] # convert to true name
                        ctxcls = contexts.get(_context_name)
                        if not ctxcls:
                            player.tell("The %s context could not be loaded remotely." % _context_name)
                            return
                        contextual = "com_%s" % command
                        context = ctxcls(self)
                        self.tabchoices = ["%s.%s" % (context_name, attribute[4:]) for attribute in dir(context) if attribute.startswith(contextual) and attribute != 'com_exit']
                        if self.tabchoices:
                            self.tabarg = 0
                            return self.handle_TAB()

                    elif isinstance(player.session.context,  contexts.get('battle')):
                        self.tabchoices = [move.selector.encode('utf8') for move in player.character.moves if move.selector.startswith(parts[0])]
                        callowed, cglobals = get_allowed(player)
                        self.tabchoices += [cname for cname in callowed if cname.startswith(parts[0])]
                        if self.tabchoices:
                            self.tabarg = 0
                            return self.handle_TAB()
                    else:
                        callowed, cglobals = get_allowed(player)
                        self.tabchoices = [cname for cname in callowed+cglobals if cname.startswith(parts[0])]
                        if self.tabchoices:
                            self.tabarg = 0
                            return self.handle_TAB()
                # complete arguments
                schema = None
                comobj = None
                callowed, cglobals = get_allowed(player)
                if len(parts) > 1:

                    if '.' in comname:
                        _parts = comname.split('.')
                        if len(_parts) == 2:
                            context_name, command = _parts
                            if context_name in ['build', 'admin'] and command != exit:
                                _context_name = {'build':'builder', 'admin':'administration'}[context_name] # convert to true name
                                ctxcls = contexts.get(_context_name)
                                if ctxcls:
                                    contextual = "com_%s" % command
                                    context = ctxcls(self)
                                    if hasattr(context, contextual):
                                        comobj = getattr(context, contextual)
                    # battle move arg
                    elif isinstance(player.session.context,  contexts.get('battle')) and len(parts) == 2:
                        moves = [move for move in player.character.moves if move.selector == comname]
                        if moves:
                            move = moves[0]
                            self.tabchoices = []
                            for fighter in self.app.game.fighters.itervalues():
                                try:
                                    self.app.game.validate_target(player, fighter, move)
                                except ValidationError: pass
                                else:
                                    self.tabchoices.append(fighter.nickname.encode('utf8'))
                            if self.tabchoices:
                                self.tabarg = 1
                                self.handle_TAB()
                    # contextual
                    elif comname in callowed:
                        contextual = "com_%s" % comname
                        if hasattr(player.session.context, contextual):
                            # get the command
                            comobj = getattr(player.session.context, contextual)
                    # global
                    elif comname in cglobals:
                        comobj = get(comname)
                    # do complete via exception
                    if comobj:
                        try:
                            data = v.command(self.app, comobj, parts[1:], player=player)
                        except v.ValidationError, e:
                            if e.choices:
                                self.tabchoices = [c.encode('utf8') for c in e.choices]
                                if self.tabchoices:
                                    self.tabarg = e.argnum
                                    self.handle_TAB()
        
    def on_lobby_command(self, command, args):
        # XXX HACK -- hardwiring builtin commands when we should have
        # a lobby context associated with temporary users instead
        if command == 'create': 
            return self.do_create(args)
        elif command == 'connect':
            return self.do_connect(args)
        else:
            self.sendLine("Unknown command.  Commands at this time are:")
            self.sendLine("   create <username> <email> <password>")
            self.sendLine("   connect <username> <password>")

    def do_connect(self, args):
        try:
            (nickname, password) = args
        except ValueError:
            self.sendLine("Usage: connect <username> <passsword>")
            return
        user = User.get(nickname=nickname)
        if not user:
            self.sendLine("No such user '%s'." % nickname)
            return
        elif user.password != password:
            self.sendLine("Incorrect password.")
            return 
        elif nickname in self.app.players:
            self.sendLine("That user is currently signed on.")
            return
        self.nickname = user.nickname
        user.naws_w = self.width
        for x in xrange(128): self.sendLine("\n")
        self.app.signals['outgoing_msg'].register(self.on_outgoing_msg)
        self.app.signals['login'].emit(self.nickname)
        self.sendLine("You are now bound to '%s'." % user.nickname)
        self.handler = self.on_command
        # self.drawInputLine()
        self.drawInput = True

    def do_create(self, args):
        try:
            (nickname, email, password) = args
        except ValueError:
            self.sendLine("Usage: create <username> <email> <password>")
            return
        u = User.get(nickname=nickname)
        if u:
            self.sendLine("Sorry, '{0}' is already taken.".format(nickname))
            return
        User.create(nickname, email, password)
        self.do_connect((nickname, password))
        
    def terminalSize(self, width, height):
        if self.nickname:
            User.get(nickname=self.nickname).naws_w = width
        self.terminal.reset()
        self.setInsertMode()
        self.width, self.height = width, height
        self.display_history = deque(self.display_history, maxlen=height)
        for line in self.display_history:
            if line:
                self.terminal.write((line+"\n").encode('utf8')[:width])
        self.drawInputLine()
        

    def on_command(self, command, args):
        self.app.do_command(self.nickname, command, args)

    def on_outgoing_msg(self, nickname, message):
        if nickname == self.nickname:
            self.sendLine(message)

    def sendLine(self, data):
        if data:
            line = (data).encode('utf8')[:self.width]
            self.display_history.append(line)
            self.terminal.deleteLine(n=2)
            self.terminal.cursorBackward(n=len(line))
            self.terminal.write((line+"\n").encode('utf8'))
            if self.drawInput:
                self.drawInputLine()
            
    def drawInputLine(self):

        promptline = self.prompt + ''.join(self.lineBuffer)
        self.terminal.write(promptline + '\n')
        self.terminal.write(self.status)
        self.terminal.cursorUp()
        pl = len(promptline)
        sl = len(self.status)
        if pl < sl:
           self.terminal.cursorBackward(n=(sl - pl))
        elif pl > sl:
           self.terminal.cursorForward(n=(pl-sl))

    def lineReceived(self, line):
        self.drawInput = False
        encoding = chardet.detect(line)['encoding']
        if encoding:
            line = line.decode(encoding)
        self.display_history.append(self.prompt + line)
        parts = line.split()
        if len(parts):
            command, args = parts[0], parts[1:]
            self.handler(command, args)
            self.drawInputLine()
            self.drawInput = True
            
class TelnetService(internet.TCPServer):
    service_name = 'telnet'
    
    def wtf(self):
        return TelnetTransport(TelnetBootstrapProtocol, ServerProtocol, TelnetProtocol, self.app)
    
    def __init__(self, app):
        self.app = app
        port = settings.TELNET_PORT
        self.factory = protocol.ServerFactory()
        self.factory.protocol = self.wtf
        internet.TCPServer.__init__(self, port, self.factory)
        
    def get_signal_matrix(self):
        return {}
