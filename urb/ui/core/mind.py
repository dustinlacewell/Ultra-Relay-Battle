from twisted.internet import defer
from twisted.python import failure, log
from twisted.python.components import Componentized, Adapter
from twisted.cred import portal, checkers, error, credentials

from zope.interface import Interface, Attribute, implements

from django.contrib.auth.models import check_password

from urb.players.models import Player
from urb.ui.core.interfaces import IUrwidMind
from urb.ui.manager import UrwidUI

class DjangoAuthChecker:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def _passwordMatch(self, matched, user):
        if matched:
            return user
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def requestAvatarId(self, credentials):
        if credentials.username.lower() == 'register':
            return defer.maybeDeferred(
                lambda u,p: True,
                credentials.password,
                None).addCallback(self._passwordMatch, None)
        try:
            player = Player.objects.get(username=credentials.username)
            return defer.maybeDeferred(
                check_password,
                credentials.password,
                player.password).addCallback(self._passwordMatch, player)
        except Player.DoesNotExist:
            return defer.fail(error.UnauthorizedLogin())


class UnhandledKeyHandler(object):

    def __init__(self, mind):
        self.mind = mind

    def push(self, key):
        if isinstance(key, tuple):
            pass
        else:
            f = getattr(self, 'key_%s' % key.replace(' ', '_'), None)
            if f is None:
                return
            else:
                return f(key)

    def key_ctrl_c(self, key):
        self.mind.terminal.loseConnection()


class UrwidMind(Adapter):

    implements(IUrwidMind)

    cred_checkers = [DjangoAuthChecker()]
    ui = None

    ui_factory = UrwidUI
    unhandled_key_factory = UnhandledKeyHandler

    def __init__(self, *args, **kwargs):
        self.app = kwargs.pop('app')
        Adapter.__init__(self, *args, **kwargs)

    @property
    def avatar(self):
        return IConchUser(self.original)

    def set_terminalProtocol(self, terminalProtocol):
        self.terminalProtocol = terminalProtocol
        self.terminal = terminalProtocol.terminal
        self.unhandled_key_handler = self.unhandled_key_factory(self)
        self.unhandled_key = self.unhandled_key_handler.push
        self.ui = self.ui_factory(self, self.app)

    def push(self, data):
        self.ui.screen.push(data)

    def draw(self):
        self.ui.loop.draw_screen()
