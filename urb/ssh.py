from twisted.cred.portal import Portal
from twisted.application.internet import TCPServer
from twisted.cred import credentials
from twisted.conch.ssh import userauth, connection
from twisted.conch import error, interfaces
from twisted.conch.manhole_ssh import ConchFactory

from urb.ui.mind import UrwidMind
from urb.ui.realm import UrwidRealm


class SSHClearAuthServer(userauth.SSHUserAuthServer):
    def tryAuth(self, kind, user, data):
        if user.lower() == 'register':
            c = credentials.UsernamePassword(user, None)
            return self.portal.login(c, None, interfaces.IConchUser).addErrback(self._ebPassword)        
        return userauth.SSHUserAuthServer.tryAuth(self, kind, user, data)

class CustomSSHFactory(ConchFactory):
    services = {
        'ssh-userauth':SSHClearAuthServer,
        'ssh-connection':connection.SSHConnection
    }    

class SSHService(TCPServer):
    service_name = 'SSH'

    def __init__(self, app):
        self.app = app
        self.realm = UrwidRealm(UrwidMind, app)
        self.portal = Portal(self.realm, UrwidMind.cred_checkers)
        self.factory = CustomSSHFactory(self.portal)
        TCPServer.__init__(self, 6060, self.factory)

    def get_signal_matrix(self):
        return {}
