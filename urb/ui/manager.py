import urwid

from urb.ui.terminal import TwistedScreen

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

    def auth_command(self, command, args):
        if command == 'create':
            pass
        elif command == 'connect':
            self.do_connect(args)
        else:
            self.msg("Unknown command.  Commands at this time are:")
            self.msg("   create <username> <email> <password>")
            self.msg("   connect <username> <password>")

    def do_connect(self, args):
        try:
            (username, password) = args
        except ValueError:
            self.msg("Usage: connect <username> <passsword>")
            return

        player = Player.objects.get(username=username)
        if not player:
            self.msg("No such user '%s'." % username)
            return

        self.session = self.app.sessions.login(username, password, self)
        if self.session is None:
            self.msg("Incorrect username and password.")
            return

        self.msg("You are now bound to '%s'." % player.username)
        # self.handler = self.on_command
        # # self.drawInputLine()
        # self.drawInput = True

    def do_create(self, args):
        try:
            (username, email, password) = args
        except ValueError:
            self.msg("Usage: create <username> <email> <password>")
            return

        u = Player.objects.get(username=username)
        if u:
            self.msg("Sorry, '{0}' is already taken.".format(username))
            return
        
        self.app.sessions.register(username, password, email)
        self.do_connect((username, password))

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
        title_txt = urwid.Text("""
Ultra Relay Battle - v 1.0
    create <username> <email> <password>
    connect <username> <password>
""", align='left')
        self.input = urwid.Edit(u"> ")
        self.output = urwid.Pile((title_txt, self.input))

        class CustomFiller(urwid.Filler):

            def __init__(this, *args, **kwargs):
                this.comm_handler = self.auth_command
                super(CustomFiller, this).__init__(*args, **kwargs)

            def msg(this, message):
                self.output.contents.insert(-1, (urwid.Text(
                    message,
                ), ('pack', None)))

            def keypress(this, size, key):
                method_name = 'handle_%s' % key.upper()
                method = getattr(this, method_name, None)
                if method:
                    if key != 'tab':
                        self.tabchoices = []
                        self.tabarg = None
                    return method(size, key)
                else:
                    return super(CustomFiller, this).keypress(size, key)                    

            def handle_ENTER(this, size, key):
                if self.input.edit_text:
                    parts = self.input.edit_text.split()
                    if len(parts) > 1:
                        this.comm_handler(parts[0], parts[1:])
                    else:
                        this.comm_handler(parts[0], tuple())
                    self.input.set_edit_text('')

        fill = CustomFiller(self.output, valign='bottom')
        return fill



