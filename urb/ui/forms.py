from __future__ import print_function

from collections import OrderedDict

import urwid
from urwid.util import is_wide_char

from urb.ui.screen import UrwidScreen
from urb.ui.console import UrwidConsole
from urb.players.models import Player
from urb.validation import *


import sys
import re
from itertools import chain

def get_focus(widget):
    child = (
        getattr(widget, 'focus', None) or 
        getattr(widget, 'original_widget', None))
    if child:
        return get_focus(child)
    return widget

class FieldAdapter(object):
    def __init__(self, *args, **kwargs):
        self.creation_counter = Field.creation_counter        
        Field.creation_counter += 1
        super(FieldAdapter, self).__init__(*args, **kwargs)

class FormHeader(FieldAdapter, urwid.Text): pass

class FormButton(FieldAdapter, urwid.Button): pass

class Field(object):

    creation_counter = 0

    validator = None    
    defaults = (
        ('label', None),
        ('initial', None),
    )

    def __init__(self, **kwargs):

        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

        self.app = None

        defaults = self.get_defaults()
        for defname, defvalue in defaults:
            if defname in kwargs:
                setattr(self, defname, kwargs.pop(defname))
            if not hasattr(self, defname):
                setattr(self, defname, dict(defaults)[defname])

        if kwargs:
            raise TypeError("Unexpected field initialization parameters: " +
                ', '.join(kwargs.keys()))

    def get_defaults(self):
        defaults = tuple()
        mro = self.__class__.__mro__
        for cls in mro:
#            print "Checking {0}".format(cls)
            if issubclass(cls, Field):
                new = getattr(cls, 'defaults', tuple())
                defaults += new
        return defaults    

    def clean(self, value):
        return value

    def validate(self, val):
        if self.__class__.validator:
            parts = val.split()
            return self.__class__.validator(self.app, self.label, parts)

    def get_widget(self, model):
        return getattr(model, "__field_{0}".format(id(self)))

    def set_widget(self, model, widget):
        setattr(model, '__field_{0}'.format(id(self)), widget)

    def get_body(self):
        raise NotImplementedError()

    def get_value(self, widget):
        raise NotImplementedError()

    def set_value(self, widget, cleaned):
        raise NotImplementedError()

    def __get__(self, model, modeltype):
        widget = self.get_widget(model)                
        return self.get_value(widget)

    def __set__(self, model, value):
        widget = self.get_widget(model)
        cleaned = self.clean(value)
        self.validate(cleaned)
        self.set_value(widget, cleaned)


class FormMeta(urwid.widget.WidgetMeta):

    def __call__(cls, *args):
        inst = super(FormMeta, cls).__call__(*args)

        for name, field in inst._fields.items():
            if isinstance(field, Field):
                field, body, widget = inst._widgets[name]
                field.set_widget(inst, body)
                if field.initial:
                    field.set_value(initial)
            elif isinstance(field, FieldAdapter):
                if isinstance(field, urwid.Button):
                    handler_name = 'pressed_{0}'.format(name.upper())
                    handler = getattr(inst, handler_name, None)
                    if handler:
                        urwid.connect_signal(field, 'click', handler)                    
                field.form = inst
        return inst

    def __new__(cls, clsname, bases, attrs):
        fields = {}
        widgets = {}
        for name, field in attrs.items():
            if isinstance(field, Field):
                body = field.get_body()
                asterisk = urwid.Text('* ')
                label = urwid.Text(field.label or name.title())
                colon = urwid.Text(': ')
                editwidget = urwid.Columns([
                    ('fixed', 2, asterisk),
                    ('weight', 1, label),
                    ('fixed', 2, colon),
                    ('weight', 10, body)
                ])
                widget = urwid.Padding(
                    editwidget, 
                    ('fixed left', 3), 
                    ('fixed right', 3)
                )
                fields[name] = field
                widgets[name] = (field, body, widget)
            elif isinstance(field, FieldAdapter):
                fields[name] = field
                widgets[name] = (field, field, field)
        fields = OrderedDict(sorted(fields.items(), 
            key=lambda (name, field): field.creation_counter))
        widgets = OrderedDict(sorted(widgets.items(), 
            key=lambda (name, field): field[0].creation_counter))
        attrs['_fields'] = fields
        attrs['_widgets'] = widgets
        return super(FormMeta, cls).__new__(cls, clsname, bases, attrs)

class UrwidForm(UrwidScreen):

    __metaclass__ = FormMeta

    def __init__(self, *args, **kwargs):
        self.note = None
        self.yank_ring = []
        super(UrwidForm, self).__init__(*args, **kwargs)

    def pressed_ok(self, button):
        raise NotImplementedError()

    def pressed_cancel(self, button):
        raise NotImplementedError()

    def set_note(self, text):
        if text:
            if self.note:
                self.note.set_text(text)
            else:
                self.note = urwid.Text(text)
                self.widgets.append((self.note, ('pack', None)))
        else:
            if self.note:
                self.widgets.remove((self.note, ('pack', None)))
                self.note = None

    def get_body(self):
        """ the body of our form, called from main() """
        widgets = []
        buttons = []
        _widgets = [w[-1] for w in self._widgets.values()]
        for widget in _widgets:
            if isinstance(widget, urwid.Button):
                buttons.append(widget)
            else:
                widgets.append(widget)
        widgets.append(urwid.GridFlow(buttons, 10, 7, 1, 'left'))
        self.pile = urwid.Pile(widgets)
        self.widgets = self.pile.contents
        return urwid.Filler(self.pile, valign='bottom')

    def keypress(self, size, key):
        print(key)

        focus = get_focus(self)        
        if isinstance(focus, urwid.Edit):
            if key == 'ctrl _':
                undos = self.undo.get(focus, [])
                if len(undos):
                    focus.set_edit_text(undos.pop())
                self.undo[focus] = undos
                return
            else:
                undos = self.undo.get(focus, [])
                undos.append(focus.edit_text)
                self.undo[focus] = undos
        super(UrwidForm, self).keypress(size, key)

    def handle_CTRLN(self, size, key):
        super(UrwidForm, self).keypress(size, 'down')
    def handle_CTRLP(self, size, key):
        super(UrwidForm, self).keypress(size, 'up')
    def handle_CTRLF(self, size, key):
        super(UrwidForm, self).keypress(size, 'right')
    def handle_CTRLB(self, size, key):
        super(UrwidForm, self).keypress(size, 'left')
    def handle_CTRLA(self, size, key):
        super(UrwidForm, self).keypress(size, 'home')
    def handle_CTRLE(self, size, key):
        super(UrwidForm, self).keypress(size, 'end')
    def handle_CTRLK(self, size, key):
        focus = get_focus(self.pile)
        if isinstance(focus, urwid.Edit):
            coord = focus.get_cursor_coords((10, ))[0]
            txt = focus.edit_text
            self.yank_ring.append(txt[coord:])
            focus.set_edit_text(txt[:coord:])

    def handle_CTRLY(self, size, key):
        focus = get_focus(self.pile)
        if isinstance(focus, urwid.Edit):
            coord = focus.get_cursor_coords((10, ))[0]
            text = self.yank_ring.pop()
            focus.insert_text(text)


    def handle_CTRLD(self, size, key):
        focus = get_focus(self.pile)
        if isinstance(focus, urwid.Edit):
            coord = focus.get_cursor_coords((10, ))[0]
            txt = focus.edit_text
            focus.set_edit_text(txt[:coord] + txt[coord + 1:])



class EditWidget(urwid.Edit):
    def __init__(self, field, *args, **kwargs):
        super(EditWidget, self).__init__(*args, **kwargs)
        self.field = field

    def valid_char(self, char):
        return self.field.valid_char(self, char)

class TextField(Field):

    validator = staticmethod(message)

    defaults = (
        ('max_length', None),
        ('single_word', False),
        ('mask', None)
    )

    def valid_char(self, widget, char):
        if self.single_word and char == ' ':
            return False

        if super(EditWidget, widget).valid_char(char):
            val = self.get_value(widget)
            try:
                self.validate(val + char)
                if self.max_length and len(val + char) > self.max_length:
                    return False
            except ValidationError:
                return False
            else:
                return True

    def get_body(self):
        return EditWidget(self, mask=self.mask)

    def get_value(self, widget):
        return widget.edit_text

    def set_value(self, widget):
        widget.set_edit_text(val)


class IntegerField(Field, urwid.IntEdit):
 
    validator = staticmethod(integer)

    def get_value(self):
        return self.value()

    def set_value(self, val):
        try:
            self.validate(val)
        except ValueError:
            return
        else:
            self.set_edit_text(val)

    def valid_char(self, char):
        val = self.get_value()
        try:
            self.validate(val + char)
        except ValidationError:
            return
        else:
            return True


class RegisterForm(UrwidForm):

    login_text = """

Ultra Relay Battle v 1.0

You appear ready for battle. Register below!
"""
    header = FormHeader(login_text)
    username = TextField(max_length=10, single_word=True)
    password = TextField(mask='*')
    email = TextField()
    ok = FormButton('  OK')
    help = FormButton('  HELP')

    def pressed_OK(self, button):
        username = self.username
        if len(username) < 3:
            self.set_note('Username must be between 3 and 10 characters.')
            return
        if Player.objects.filter(username=username).count():
            self.set_note('That username is taken.')
            return

        password = self.password
        if len(password) < 12:
            self.set_note('Password must be at least 12 characters.')
            return

        email = self.email
        if '@' not in email:
            self.set_note('Please provide a valid email.')
            return

        self.ui.set_urwid_toplevel(UrwidConsole(self.app, self.session, self.ui))

    def pressed_HELP(self, button):
        self.ui.push_urwid_toplevel(HelpForm(self.app, self.session, self.ui))

class HelpForm(UrwidForm):
    help_text = """

Hey, welcome to Ultra Relay Battle!

SIGN UP                                      -
To sign up for an account you're going to need
to provide a Username and Password. Then we'll
send you an email to the provided address and
it'll contain a link. Clicking on that link
will activate your account.
    
LOG IN                                       -
To login, you can use SSH to connect to the
server:

    $ ssh youruser@ldlework.com

It'll ask you for your password. Get it right
and you'll be logged in!

(Windows users: check out the 'Putty' program)
"""

    header = FormHeader(help_text)
    ok = FormButton('  OK')

    def pressed_OK(self, button):
        self.ui.pop_urwid_toplevel()
