from zope.interface import Interface, Attribute

class IUrwidUI(Interface):

    """Toplevel urwid widget
    """
    toplevel = Attribute('Urwid Toplevel Widget')
    palette = Attribute('Urwid Palette')
    screen = Attribute('Urwid Screen')
    loop = Attribute('Urwid Main Loop')

    def create_urwid_toplevel():
        """Create a toplevel widget.
        """

    def create_urwid_mainloop():
        """Create the urwid main loop.
        """


class IUrwidMind(Interface):
    ui = Attribute('')
    terminalProtocol = Attribute('')
    terminal = Attribute('')
    checkers = Attribute('')
    avatar = Attribute('The avatar')

    def push(data):
        """Push data"""

    def draw():
        """Refresh the UI"""

