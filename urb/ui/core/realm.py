from twisted.conch.interfaces import IConchUser, ISession
from twisted.python.components import Componentized, Adapter
from twisted.conch.insults.insults import TerminalProtocol, ServerProtocol
from twisted.conch.manhole_ssh import (
    ConchFactory, TerminalRealm, TerminalUser, 
    TerminalSession, TerminalSessionTransport
)

from urb.ui.core.interfaces import IUrwidMind, IUrwidUI
from urb.ui.core.terminal import UrwidTerminalProtocol

class UrwidServerProtocol(ServerProtocol):
    def dataReceived(self, data):
        self.terminalProtocol.dataReceived(data)

class UrwidUser(TerminalUser):
    """A terminal user that remembers its avatarId

    The default implementation doesn't
    """
    def __init__(self, original, avatarId):
        TerminalUser.__init__(self, original, avatarId)
        self.avatarId = avatarId


class UrwidTerminalSession(TerminalSession):
    """A terminal session that remembers the avatar and chained protocol for
    later use. And implements a missing method for changed Window size.

    Note: This implementation assumes that each SSH connection will only
    request a single shell, which is not an entirely safe assumption, but is
    by far the most common case.
    """

    def openShell(self, proto):
        """Open a shell.
        """
        self.chained_protocol = UrwidServerProtocol(
            UrwidTerminalProtocol, IUrwidMind(self.original))
        TerminalSessionTransport(
            proto, self.chained_protocol,
            IConchUser(self.original),
            self.height, self.width)

    def windowChanged(self, (h, w, x, y)):
        """Called when the window size has changed.
        """
        self.chained_protocol.terminalProtocol.terminalSize(h, w)


class UrwidRealm(TerminalRealm):
    """Custom terminal realm class-configured to use our custom Terminal User
    Terminal Session.
    """
    def __init__(self, mind_factory, app):
        self.app = app
        self.mind_factory = mind_factory

    def _getAvatar(self, avatarId):
        comp = Componentized()
        user = UrwidUser(comp, avatarId)
        comp.setComponent(IConchUser, user)
        sess = UrwidTerminalSession(comp)
        comp.setComponent(ISession, sess)
        mind = self.mind_factory(comp, app=self.app)
        comp.setComponent(IUrwidMind, mind)
        return user

    def requestAvatar(self, avatarId, mind, *interfaces):
        for i in interfaces:
            if i is IConchUser:
                return (IConchUser,
                        self._getAvatar(avatarId),
                        lambda: None)
        raise NotImplementedError()


