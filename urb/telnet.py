import chardet, struct, collections                  # detect
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

from urb.db import *
from urb import app
from urb.util import dlog
from urb.commands import get_allowed, get
from urb import validation as v
from urb.constants import MLW
from urb import contexts

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
          
        HistoricRecvLine.__init__(self)
        
    def _get_prompt(self):
        return self.ps[self.pn]
    prompt = property(_get_prompt)
    
    def _get_status(self):
        if self.nickname and self.nickname in self.app.players:
            player = self.app.players[self.nickname]
            if isinstance(player.session.context,  contexts.get('battle')):
                
                return "# {p.health} HP : {p.magicpoints} MP : {p.superpoints} SP #".format(p=player)
            else:
                return "Ultra Relay Battle 0.9"
        else:
            return "Ultra Relay Battle 0.9"
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
            return HistoricRecvLine.handle_RETURN(self)
        
    def handle_TAB(self):
        if self.nickname: # only tab once logged in
            parts = ''.join(self.lineBuffer).split(' ')
            print 'parts are ', repr(parts)
            print 'tabchoices are ', repr(self.tabchoices)
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
                print 'parts are now ', parts
                newline = ' '.join(parts)
                print 'newline is ', repr(newline)
                end = len(' '.join(parts[:self.tabarg + 1]))
                 
                for c in newline:
                    HistoricRecvLine.characterReceived(self, c, None)
                
                diff = abs(end - self.lineBufferIndex)
                print 'arg, index, end, diff:  ', self.tabarg, self.lineBufferIndex, end, diff
                
                for x in xrange(diff):
                    self.handle_LEFT()
                    
            else: # determine tabchoices
                # complete commands
                if len(parts) == 1:
                    if isinstance(player.session.context,  contexts.get('battle')):
                        self.tabchoices = [move.selector.encode('utf8') for move in player.character.moves if move.selector.startswith(parts[0])]
                        if self.tabchoices:
                            self.tabarg = 0
                            return self.handle_TAB()
                    else:
                        callowed, cglobals = get_allowed(player)
                        self.tabchoices = [cname for cname in callowed+cglobals if cname.startswith(parts[0])]
                        if self.tabchoices:
                            print 0, self.tabchoices
                            self.tabarg = 0
                            return self.handle_TAB()
                # complete arguments
                schema = None
                comobj = None
                if len(parts) > 1:
                    print 'determining argument tab'
                    callowed, cglobals = get_allowed(player)
                    # contextual
                    if comname in callowed:
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
                                print e, dir(e)
                                self.tabchoices = [c.encode('utf8') for c in e.choices]
                                if self.tabchoices:
                                    print e.argnum, self.tabchoices
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
            self.drawInputLine()

    def do_connect(self, args):
        try:
            (nickname, password) = args
        except ValueError:
            self.sendLine("Usage: connect <username> <passsword>")
            self.drawInputLine()
            return
        user = User.get(nickname=nickname)
        if not user:
            self.sendLine("No such user '%s'." % nickname)
            self.drawInputLine()
            return
        elif user.password != password:
            self.sendLine("Incorrect password.")
            self.drawInputLine()
            return 
        self.nickname = user.nickname
        user.naws_w = self.width
        for x in xrange(128): self.sendLine("\n")
        self.app.signals['outgoing_msg'].register(self.on_outgoing_msg)
        self.app.signals['login'].emit(self.nickname)
        self.sendLine("You are now bound to '%s'." % user.nickname)
        self.handler = self.on_command
        #self.drawInputLine()

    def do_create(self, args):
        try:
            (nickname, email, password) = args
        except ValueError:
            self.sendLine("Usage: create <username> <email> <password>")
            self.drawInputLine()
            return
        u = User.get(nickname=nickname)
        if u:
            self.sendLine("Sorry, '{0}' is already taken.".format(nickname))
            self.drawInputLine()
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
        #self.drawInputLine()

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
            
    def drawInputLine(self):
        print traceback.print_stack()

        promptline = self.prompt + ''.join(self.lineBuffer)
        self.terminal.write(promptline + '\n')
        status = "{0:-^{1}}".format(self.status, min(MLW + 2, self.width))
        self.terminal.write(status)
        self.terminal.cursorUp()
        pl = len(promptline)
        sl = len(status)
        if pl < sl:
           self.terminal.cursorBackward(n=(sl - pl))
        elif pl > sl:
           self.terminal.cursorForward(n=(pl-sl))

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
