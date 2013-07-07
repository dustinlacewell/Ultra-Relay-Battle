import urwid

from urb.ui.screen import UrwidScreen

class UrwidConsole(UrwidScreen):
    def __init__(self, *args, **kwargs):
        super(UrwidConsole, self).__init__(*args, **kwargs)
        self.reset_tab()

    def reset_tab(self):
        self.tabchoices = []
        self.tabarg = None

    def pre_handle_key(self, size, key, handler):
        if key != 'tab':
            self.reset_tab()

    def msg(self, message):
        self.output.insert(-1, urwid.Text(message))
        self.items.set_focus(len(self.output) - 1)

    def get_body(self):
        self.input = urwid.Edit(u"> ")
        padding = urwid.Text('\n' * self.ui.screen.get_cols_rows()[1] * 2)
        self.output = urwid.SimpleFocusListWalker([padding, self.input])
        self.items = urwid.ListBox(self.output)
        self.items.set_focus(len(self.output) - 1)
        return self.items

    def handle_ENTER(self, size, key):
        if self.input.edit_text:
            parts = self.input.edit_text.split()
            # if len(parts) > 1:
            #     self.comm_handler(parts[0], parts[1:])
            # else:
            #     self.comm_handler(parts[0], tuple())
            self.msg(self.input.edit_text)
            self.input.set_edit_text('')

