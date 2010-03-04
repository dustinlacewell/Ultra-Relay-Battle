import chardet, struct, collections                  # detect
from collections import deque

from twisted.application import internet
from twisted.conch.telnet import TelnetTransport, TelnetProtocol, TelnetBootstrapProtocol
from twisted.conch.insults.helper import TerminalBuffer
from twisted.conch.insults.insults import ServerProtocol
from twisted.conch.recvline import HistoricRecvLine
from twisted.internet import protocol
from twisted.protocols import basic
from twisted.internet.protocol import ServerFactory

from urb.db import *
from urb import app
from urb.util import dlog
from urb.commands import get_allowed, get
from urb import validation as v

class TelnetProtocol(HistoricRecvLine):

    delimiter = '\n'
    ps = ['> ']        

    def __init__(self, app):
        self.app = app
        self.handler = self.on_lobby_command
        self.nickname = None
        self.display_history = deque()
        self.tabchoices = []
          
        HistoricRecvLine.__init__(self)
        
    def _get_prompt(self):
        return self.ps[self.pn]
    prompt = property(_get_prompt)
    
    def initializeScreen(self):
        self.terminal.reset()
        self.terminal.write(self.prompt)
        self.sendLine("Ultra Relay Battle - conch interface :")
        self.sendLine("   create <username> <email>")
        self.sendLine("   connect <username>")
        self.drawInputLine()
        self.setInsertMode()
        
    def characterReceived(self, ch, moreCharactersComing):
        self.tabchoices = []
        HistoricRecvLine.characterReceived(self, ch, moreCharactersComing)
        
    def handle_BACKSPACE(self):
        self.tabchoices = []
        HistoricRecvLine.handle_BACKSPACE(self)
        
    def handle_TAB(self):
        print self.tabchoices
        parts = ''.join(self.lineBuffer).split(' ')
        player = self.app.players[self.nickname]
        if self.tabchoices:
            self.tabchoices.append( self.tabchoices.pop(0) )
            choice = self.tabchoices[0]
            for x in range(len(parts[-1])):
                HistoricRecvLine.handle_BACKSPACE(self)
            for c in choice:
                HistoricRecvLine.characterReceived(self, c, None)
        else:
            if len(parts) == 1:
                if not self.tabchoices:
                    callowed, cglobals = get_allowed(player)
                    self.tabchoices = [cname for cname in callowed+cglobals if cname.startswith(parts[0])]
                    self.handle_TAB()
            schema = None
            if len(parts) > 1:
                callowed, cglobals = get_allowed(player)
                comname = parts[0]
                comobj = None
                if comname in callowed:
                    contextual = "com_%s" % comname
                    if hasattr(player.session.context, contextual):
                        # get the command
                        comobj = getattr(player.session.context, contextual)
                elif comname in cglobals:
                    comobj = get(comname)
                if comobj:
                    try:
                        data = v.command(self, comobj, parts[1:])
                    except v.ValidationError, e:
                        if e.choices:
                            self.tabchoices = [e.encode('utf8') for e in e.choices]
                            self.handle_TAB()
                
                        
        
        #=======================================================================
        # n = self.TABSTOP - (len(self.lineBuffer) % self.TABSTOP)
        # self.terminal.cursorForward(n)
        # self.lineBufferIndex += n
        # self.lineBuffer.extend(' ' * n)
        #=======================================================================
        
    def on_lobby_command(self, command, args):
        # XXX HACK -- hardwiring builtin commands when we should have
        # a lobby context associated with temporary users instead
        if command == 'create': 
            return self.do_create(args)
        elif command == 'connect':
            return self.do_connect(args)
        else:
            self.sendLine("Unknown command.  Commands at this time are:")
            self.sendLine("   create <username> <email>")
            self.sendLine("   connect <username>")
            self.drawInputLine()

    def do_connect(self, args):
        try:
            (nickname,) = args
        except ValueError:
            self.sendLine("Usage: connect <username>")
            self.drawInputLine()
            return
        user = User.get(nickname=nickname)
        if not user:
            self.sendLine("No such user '%s'." % nickname)
            self.drawInputLine()
            return

        self.nickname = user.nickname
        user.naws_w = self.width
        self.app.signals['outgoing_msg'].register(self.on_outgoing_msg)
        self.app.signals['login'].emit(self.nickname)
        self.sendLine("You are now bound to '%s'." % user.nickname)
        self.handler = self.on_command
        self.drawInputLine()

    def do_create(self, args):
        try:
            (nickname, email) = args
        except ValueError:
            self.sendLine("Usage: create <username> <email>")
            return
        User.create(nickname, email)
        self.sendLine("New user '%s' created successfully" % nickname)
        
    def terminalSize(self, width, height):
        if self.nickname:
            User.get(nickname=self.nickname).naws_w = width
        self.terminal.eraseDisplay()
        self.terminal.cursorHome()
        self.width = width
        self.height = height
        self.display_history = deque(self.display_history, maxlen=height)
        for line in self.display_history:
            if line:
                self.terminal.write((line+"\n").encode('utf8')[:width])
        

    def on_command(self, command, args):
        self.app.do_command(self.nickname, command, args)
        self.drawInputLine()

    def on_outgoing_msg(self, nickname, message):
        if nickname == self.nickname:
            self.sendLine(message)

    def sendLine(self, data):
        if data:
            line = (data).encode('utf8')[:self.width]
            self.display_history.append(line)
            self.terminal.write((line+"\n").encode('utf8'))

    def lineReceived(self, line):
        encoding = chardet.detect(line)['encoding']
        if encoding:
            line = line.decode(encoding)
        self.display_history.append(self.prompt + line)
        parts = line.split()
        if len(parts):
            command, args = parts[0], parts[1:]
            self.handler(command, args)
        
            
class TelnetService(internet.TCPServer):
    service_name = 'telnet'
    
    def wtf(self):
        return TelnetTransport(TelnetBootstrapProtocol, ServerProtocol, TelnetProtocol, self.app)
    
    def __init__(self, app):
        self.app = app
        port = get_config().telnet_port
        self.factory = protocol.ServerFactory()
        self.factory.protocol = self.wtf
        internet.TCPServer.__init__(self, port, self.factory)
        
    def get_signal_matrix(self):
        return {}
