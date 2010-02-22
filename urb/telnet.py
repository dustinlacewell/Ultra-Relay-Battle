import chardet                  # detect

from twisted.application import internet
from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet import protocol
from twisted.protocols import basic

from urb import app
from urb.util import dlog

class TelnetSession(basic.LineReceiver, TelnetProtocol):

    delimiter = '\n'

    def __init__(self, app):
        self.app = app
        self.handler = self.on_lobby_command
        self.nickname = None

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
        user = self.app.database.get_user(nickname)
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
        self.app.database.new_user(nickname, email)
        self.app.database.commit()
        self.sendLine("New user '%s' created successfully" % nickname)


    def on_command(self, command, args):
        self.app.do_command(self.nickname, command, args)

    def on_outgoing_msg(self, nickname, message):
        if nickname == self.nickname:
            self.sendLine(message)

    def sendLine(self, data):
        basic.LineReceiver.sendLine(self, "# %s" % data.encode('utf8'))

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
        port = app.database.get_config().telnet_port
        self.factory = protocol.ServerFactory()
        self.factory.protocol = self.wtf
        internet.TCPServer.__init__(self, port, self.factory)
        
    def get_signal_matrix(self):
        return {}
