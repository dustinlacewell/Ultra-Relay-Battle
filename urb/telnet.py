import chardet, struct                  # detect

from twisted.application import internet
from twisted.conch.telnet import TelnetTransport, TelnetProtocol, TelnetBootstrapProtocol
from twisted.internet import protocol
from twisted.protocols import basic

from urb.db import *
from urb import app
from urb.util import dlog

class TelnetSession(basic.LineReceiver, TelnetBootstrapProtocol):

    delimiter = '\n'        

    def __init__(self, app):
        self.app = app
        self.handler = self.on_lobby_command
        self.nickname = None   
        print dir(self) 

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

    def do_connect(self, args):
        try:
            (nickname,) = args
        except ValueError:
            self.sendLine("Usage: connect <username>")
            return
        user = User.get(nickname=nickname)
        if not user:
            self.sendLine("No such user '%s'." % nickname)
            return

        self.nickname = user.nickname
        self.app.signals['outgoing_msg'].register(self.on_outgoing_msg)
        self.app.signals['login'].emit(self.nickname)
        self.sendLine("You are now bound to '%s'." % user.nickname)
        self.handler = self.on_command

    def do_create(self, args):
        try:
            (nickname, email) = args
        except ValueError:
            self.sendLine("Usage: create <username> <email>")
            return
        User.create(nickname, email)
        self.sendLine("New user '%s' created successfully" % nickname)
        
    #===========================================================================
    # def telnet_NAWS(self, bytes):
    #    # NAWS is client -> server *only*.  self.protocol will
    #    # therefore be an ITerminalTransport, the `.protocol'
    #    # attribute of which will be an ITerminalProtocol.  Maybe.
    #    # You know what, XXX TODO clean this up.
    #    print "*"*1000
    #    if len(bytes) == 4:
    #        width, height = struct.unpack('!HH', ''.join(bytes))
    #        User.get(nickname=nickname).naws_w = width
    #    else:
    #        log.msg("Wrong number of NAWS bytes")
    #===========================================================================


    def on_command(self, command, args):
        self.app.do_command(self.nickname, command, args)
        self.transport.write(">")
        print "***********", dir(self)

    def on_outgoing_msg(self, nickname, message):
        if nickname == self.nickname:
            self.sendLine(message)

    def sendLine(self, data):
        basic.LineReceiver.sendLine(self, data.encode('utf8'))

    def dataReceived(self, data):
        encoding = chardet.detect(data)['encoding']
        if encoding:
            basic.LineReceiver.dataReceived(self, data.decode(encoding))
        else: 
            basic.LineReceiver.dataReceived(self, data)

    def lineReceived(self, line):
        parts = line.split()
        if len(parts):
            command, args = parts[0], parts[1:]
            self.handler(command, args)
        
            
class TelnetService(internet.TCPServer):
    service_name = 'telnet'
    
    def wtf(self):
        return TelnetTransport(TelnetSession, self.app)
    
    def __init__(self, app):
        self.app = app
        port = get_config().telnet_port
        self.factory = protocol.ServerFactory()
        self.factory.protocol = self.wtf
        internet.TCPServer.__init__(self, port, self.factory)
        
    def get_signal_matrix(self):
        return {}
