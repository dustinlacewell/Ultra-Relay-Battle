import urwid

from urb.ui.screen import UrwidScreen

class UrwidConsole(UrwidScreen):
    def __init__(self, *args, **kwargs):
        kwargs['height'] = 'flow'
        super(UrwidConsole, self).__init__(*args, **kwargs)
        self.reset_tab()

    def reset_tab(self):
        self.tabchoices = []
        self.tabarg = None

    def pre_handle_key(self, size, key, handler):
        if key != 'tab':
            self.reset_tab()

    def msg(self, message):
        self.output.contents.insert(-1, (urwid.Text(
            message,
        ), ('pack', None)))
        self.adapter.height += 1

    def get_body(self):
        self.input = urwid.Edit(u"> ")
        self.output = urwid.SimpleListWalker([self.input])
        self.adapter = urwid.BoxAdapter(urwid.ListBox(self.output), 1)
        return self.output

    def handle_ENTER(self, size, key):
        if self.input.edit_text:
            parts = self.input.edit_text.split()
            # if len(parts) > 1:
            #     self.comm_handler(parts[0], parts[1:])
            # else:
            #     self.comm_handler(parts[0], tuple())
            self.msg(self.input.edit_text)
            self.input.set_edit_text('')

