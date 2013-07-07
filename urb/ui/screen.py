
import urwid

class UrwidScreen(urwid.LineBox):
    def __init__(self, app, session, ui, *args, **kwargs):
        self.app = app
        self.session = session
        self.ui = ui
        self.body = self.get_body()
        self.undo = {}
        super(UrwidScreen, self).__init__(self.body, *args, **kwargs)

    def pre_handle_key(self, size, key, handler):
        pass

    def keypress(self, size, key):
        key = key.replace(' ', '')
        method_name = 'handle_%s' % key.upper()
        method = getattr(self, method_name, None)
        if method:
            self.pre_handle_key(size, key, method)
            return method(size, key)
        else:
            return super(UrwidScreen, self).keypress(size, key)                    

    def get_body(self):
        raise NotImplementedError()
