import chardet                  # detect
import socket                   # inet_aton
import struct                   # unpack

from twisted.application import internet
from twisted.internet import reactor, protocol
from twisted.persisted import styles
from twisted.protocols import basic
from twisted.words.protocols.irc import IRCClient, DccChat

from urb.db import *
from urb import app
from urb.colors import colorize
from urb.util import dlog

NUL = chr(0)
CR = chr(015)
NL = chr(012)
LF = NL
SPC = chr(040)


class IRCBot(IRCClient):
    lineRate = None
    # Currently joined channels
    channels = set() 
    # Nicknames to ignore
    ignore = set(['NickServ', 'ChanServ']) 
    # Default nickname for bot
    nickname = 'TheHost' 
    # A set of pending whois binds
    pending_binds = set()
    # A mapping of remote host addresses to nicks
    remote_hosts = {}
    
    # Unicode IO conversions and colorization
    def sendLine(self, line):
        line = colorize(line)
        line = line.encode('utf8')
        IRCClient.sendLine(self, line)
        
    def dataReceived(self, data):
        encoding = chardet.detect(data)['encoding']
        udata = data.decode(encoding)
        IRCClient.dataReceived(self, udata)
            
    def connectionMade(self):
        dlog("Successfully connected to %s" % self.network)
        IRCClient.connectionMade(self)
        
    # Perform on connect
    def signedOn(self):
        # Join channels
        self.join(self.mainchannel)
        self.join(self.logchannel)
        self.msg('ChanServ', "op %s" % self.logchannel)
        # Mark service as signed on
        self.factory.signed_on = True
        dlog("Succesfully logged on as %s" % self.nickname)
        
    def joined(self, channel):
        dlog('Joined %s' % channel)
        self.channels.add(channel)
        
    def left(self, channel):
        dlog('Parted %s' % channel)
        if channel in self.channels:
            self.channels.remove(channel)
            
    # Built in command handling        
    def builtin(self, nickname, command, args):
        if command == 'register': # add new user
            email = args[0]
            User.create(nickname, email)
            self.msg(nickname, "New user, %s, created." % nickname)
            self.msg(nickname, "Please initiate a DCC Chat to login.")
            return True  
        
    
    # Incomming message handling    
    def privmsg(self, user, channel, message):
        dlog('[%s]%s said, "%s"' % (channel, user, message))
        nickname = user.split('!', 1)[0]
        # Filter messages
        if channel != self.nickname: return # only true private messages
        if nickname in self.ignore: return # reject ignored nicknames
        if not user.strip(): return # reject blank nicks
        if message.startswith('DCC'): return # ignore DCC messages
        # Parse message into command and args
        parts = message.split()
        command, args = parts[0], parts[1:]
        
        # If command was admin built in return
        if self.builtin(nickname, command, args): return
        
        # If registered, direct to DCC Chat
        if User.get(nickname=nickname):
            self.msg(nickname, 'Please initiate DCC Chat to begin.')
        # Otherwise direct to registration
        else:
            self.msg(nickname, 'Welcome %s to Ultra Relay Battle!' % nickname)
            self.msg(nickname, 'To register type the following:')
            self.msg(nickname, '       /msg %s register [email]' % self.nickname)
    
    # Respond to DCC invites           
    def dccDoChat(self, user, channel, address, port, data):
        user = user.split('!', 1)[0]
        dlog('DCC Chat request from %s on %s:%s' % (user, str(address), str(port)))
        u = User.get(nickname=user)
        if u:
            self.remote_hosts[str(address)] = unicode(user)
            self.bind(user)
        else:
            self.msg(user, "You must be registered to login.")
            self.msg(user, "To register type the following:")
            self.msg(user, "/msg %s register [email]" % self.nickname)
            
    # Initiate binding process via WHOIS lookup        
    def bind(self, nickname):
        dlog('Requesting whois information on %s for bind' % nickname)
        self.pending_binds.add(nickname) # Add nickname to people waiting for DCC
        self.sendLine('WHOIS %s' % nickname) # Request WHOIS info for nickname
        
    # Continue bind process in response to WHOIS results    
    def irc_330(self, prefix, params):
        nickname = params[1]
        message = params[2]
        dlog('Whois information received for %s' % nickname)
        # If pending and identified then bind
        if 'is logged in as' in params and nickname in self.pending_binds:
            dlog('Whois confired %s is identified to services' % nickname)
            self.dccChat(nickname) # initiate DCC Chat
            self.pending_binds.remove(params[1]) # nickname is no longer pending
        # Inform user NickServ identification is required    
        elif nickname in self.pending_binds:
            self.msg(nickname, "To establish DCC login, you *must* be identified to NickServ.")
            self.msg(nickname, "See '/msg nickserv help'")  
    
    # Initiate a DCC Chat session        
    def dccChat(self, nickname):
        dlog("Sending DCC invite with %s" % self.dccargs)
        self.ctcpMakeQuery(nickname.encode('utf8'), [('DCC', self.dccargs)])


class DccChat(basic.LineReceiver, styles.Ephemeral):
    """Direct Client Connection protocol type CHAT."""
    delimiter = NL
    bot = None
    buffer = ""
    globalcoms = ['notice']
 
    # DCC Chat is succesfully connected
    def connectionMade(self):
        dlog("Established DCC Chat with %s" % self.remote_nick)
        self.factory.bind(self.remote_nick, self)
        
    # DCC Chat ended 
    def connectionLost(self, reason=None):
        self.factory.unbind(self.remote_nick)
        dlog("Lost DCC connection with %s" % self.remote_nick)

    def sendLine(self, line):
        line = colorize(line)
        line = line.encode('utf8')
        basic.LineReceiver.sendLine(self, line)

    def dataReceived(self, data):
        encoding = chardet.detect(data)['encoding']
        udata = data.decode(encoding)
        self.buffer = self.buffer + udata
        lines = self.buffer.split(LF)
        self.buffer = lines.pop()

        for line in lines:
            if line[-1] == CR:
                line = line[:-1]
            self.lineReceived(line)

    # DCC Chat has received a line
    def lineReceived(self, line):
        dlog("%s said via DCC: %s" % (self.remote_nick, line))
        parts = line.split()
        command, args = parts[0], parts[1:]
        #try:
        self.app.do_command(self.remote_nick, command, args)
        #except Exception, e:
        #    self.sendLine("An unhandled error has occured.")
        #    dlog("Error resulted from command emission from %s for %s %s" %
        #    (self.remote_nick, command, args))
        #    self.sendLine("**** %s : %s" % (e.__class__, e.message)) 
        #    dlog("**** %s : %s" % (e.__class__, e.message)) 

class DccChatFactory(protocol.ClientFactory):
    protocol = DccChat
    client = None
    noisy = 0
    
    def __init__(self, app, ircfactory):
        # Save reference to application
        self.app = app
        # Store reference to IRC factory
        self.ircfactory = ircfactory
        
    def buildProtocol(self, addr):
        print dir(addr)
        client = self.protocol()
        client.app = self.app
        client.factory = self
        client.bot = self.ircfactory.client # Give access to IRC bot
        self.client = client
        try:
            client.remote_nick = client.bot.remote_hosts.pop(addr.host)
        except KeyError:
            self.msg("""****
    Sorry, your DCC request could not be completed for technical reasons.
    Luckily, this is easy to fix!
    
    Please refer to http://ldlework.com/wiki/urb/design#TheDCCIPProblem to
    learn how to configure your IRC client's external IP address.
    
    Seek further assistance in #urb if needed!
    Thanks.
    """)
            return None
        else:
            return self.client
        
    def clientConnectionFailed(self, unused_connector, unused_reason):
        dlog("DCC Chat connection failed to %s" % (unused_reason))
        self.client = None
        
    def clientConnectionLost(self, unused_connector, unused_reason):
        dlog("DCC Chat connection lost to %s" % (unused_reason))
        self.unbind(self.client.remote_nick)
        self.client = None
        
    def msg(self, message):
        if self.client:
            self.client.sendLine(message)
           
    def bind(self, nickname, session):
        self.ircfactory.bind(nickname, session)
        
    def unbind(self, nickname):
        self.ircfactory.unbind(nickname)
            
class IRCBotFactory(protocol.ReconnectingClientFactory):
    protocol = IRCBot
    client = None
    signed_on = False
    maxDelay = 15
    
    def __init__(self, app, ports):
        # Save reference to application
        self.app = app
        # Cycle of ports to attempt
        self.ports = ports
        # A list of DCC chats 
        self.chats = {}
        
        # Get IRC configuration
        self.conf = get_config()
        # Create DCC listen port and factory
        dccfactory = DccChatFactory(app, self)
        port = reactor.listenTCP(int(self.conf.dcc_listen_port), dccfactory, 999)
        my_address = socket.inet_aton(self.conf.dcc_listen_ip)
        my_address = struct.unpack("!I", my_address)[0]
        self.dccargs = ['CHAT', 'chat', my_address, str(self.conf.dcc_listen_port)]
        
    def dataReceived(self, data):
        try:
            protocol.ReconnectingClientFactory.dataReceived(self, data)
        except:
            pass
            
    def buildProtocol(self, addr):
        # Setup the IRC client protocol
        conf = self.conf
        client = self.protocol()
        client.app = self.app
        client.factory = self
        client.network = conf.irc_network
        client.nickname = conf.irc_nick
        client.password = conf.irc_nick_pass
        client.mainchannel = conf.irc_main_channel
        client.logchannel = conf.irc_log_channel
        client.channelpass = conf.irc_channel_pass
        # DCC invite parameters
        client.dccip = conf.dcc_listen_ip
        client.dccport = conf.dcc_listen_port
        client.dccargs = self.dccargs
        self.client = client
        return self.client
        
    def stopFactory(self):
        self.signed_on = False
    
    # Rotate the ports
    def next_port(self):
        last = self.ports.pop(0)
        self.ports.append(last)
        return self.ports[0]
        
    def clientConnectionFailed(self, connector, reason):
        dlog("IRC Client failed to connect : %s" % reason)
        self.client = None
        connector.port = self.next_port()
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        
    # DCC SESSION #
    def bind(self, nickname, session):
        u = User.get(nickname=nickname)
        if u:
            self.chats[nickname] = session
            self.app.signals['login'].emit(nickname)
            
            
    def unbind(self, nickname):
        if nickname in self.chats:
            session = self.chats.pop(nickname)
            if session:
                session.sendLine("<red>Goodbye!")
                self.app.signals['logout'].emit(nickname)

            
    # APP EVENT HANDLERS #
    def get_signal_matrix(self):
        return {
            'quit' : self.on_quit,
            'outgoing_msg' : self.on_outgoing_msg,
        }
        
    def on_quit(self, reason):
        self.client.quit(message = reason)
        self.stopTrying()
        
    def on_outgoing_msg(self, dest, msg):
        if self.client:
            if dest in self.chats:
                self.chats[dest].sendLine(msg)
            elif dest.startswith('#'):
                self.client.msg(dest, msg)
            
            
class IRCService(internet.TCPClient):
    service_name = 'irc'
    
    def __init__(self, app):
        self.app = app
        conf = get_config()
        network = conf.irc_network
        ports = [int(port) for port in conf.irc_ports]
        self.factory = IRCBotFactory(app, ports)
        internet.TCPClient.__init__(self, network, ports[0], self.factory)
        
    def get_signal_matrix(self):
        return self.factory.get_signal_matrix()
        
    def startService(self):
        self.factory.resetDelay()
        internet.TCPClient.startService(self)
        
    def stopService(self):
        self.factory.stopTrying()
        internet.TCPClient.stopService(self)
        
    # Informational Methods
    
    def is_connected(self):
        return self.factory.signed_on
        
    def channels(self):
        client = self.factory.client
        return client.channels
        
