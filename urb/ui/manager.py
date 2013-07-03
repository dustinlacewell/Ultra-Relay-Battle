import urwid

from urb.ui.core.terminal import TwistedScreen
from urb.ui.console import UrwidConsole
from urb.ui.forms import RegisterForm

class UrwidUI(object):

    def __init__(self, mind, app):
        self.app = app
        self.session = None
        self.mind = mind
        self.toplevel = self.create_urwid_toplevel()
        self.palette = self.create_urwid_palette()
        self.screen = TwistedScreen(self.mind.terminalProtocol)
        self.loop = self.create_urwid_mainloop()

    def msg(self, message):
        self.toplevel.msg(message)


    def create_urwid_mainloop(self):
        evl = urwid.TwistedEventLoop(manage_reactor=False)
        loop = urwid.MainLoop(self.toplevel, screen=self.screen,
                              event_loop=evl,
                              unhandled_input=self.mind.unhandled_key,
                              palette=self.palette)
        self.screen.loop = loop
        loop.run()
        return loop

    def create_urwid_palette(self):
        return

    def create_urwid_toplevel(self):
        return urwid.LineBox(RegisterForm(self.app, self.session, self))
        #return UrwidConsole(self.app, self.session, self)

    def set_urwid_toplevel(self, widget):
        self.loop.widget = widget