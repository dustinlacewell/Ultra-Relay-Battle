import urwid

from urb.ui.screen import UrwidScreen
from urb.ui.console import UrwidConsole


class FieldManager(object):
    """ 
    This class manages the field data without being entangled in the 
    implementation details of the widget set.
    """
    def __init__(self):
        self.getters = {}

    def set_getter(self, name, function):
        """ 
        This is where we collect all of the field getter functions.
        """
        self.getters[name] = function
        
    def get_value(self, name):
        """
        This will actually get the value associated with a field name.
        """
        return self.getters[name]()

    def get_value_dict(self):
        """
        Dump everything we've got.
        """
        retval = {}
        for key in self.getters:
            retval[key] = self.getters[key]()
        return retval

class UrwidForm(UrwidScreen):

    def __init__(self, *args, **kwargs):
        self.fieldmgr = FieldManager()
        super(UrwidForm, self).__init__(*args, **kwargs)

    def get_field(self, labeltext, inputname, fieldtype, fieldmgr):
        """ Build a field in our form.  Called from get_body()"""
        # we don't have hanging indent, but we can stick a bullet out into the 
        # left column.
        asterisk = urwid.Text('* ')
        label = urwid.Text(labeltext)
        colon = urwid.Text(': ')

        if fieldtype == 'text':
            field = urwid.Edit('', '')
            def getter():
                """ 
                Closure around urwid.Edit.get_edit_text(), which we'll
                use to scrape the value out when we're all done.
                """
                return field.get_edit_text()
            fieldmgr.set_getter(inputname, getter)
        elif fieldtype == 'checkbox':
            field = urwid.CheckBox('')
            def getter():
                """ 
                Closure around urwid.CheckBox.get_state(), which we'll
                use to scrape the value out when we're all done. 
                """
                return field.get_state()
            fieldmgr.set_getter(inputname, getter)

        # put everything together.  Each column is either 'fixed' for a fixed width,
        # or given a 'weight' to help determine the relative width of the column
        # such that it can fill the row.
        editwidget = urwid.Columns([('fixed', 2, asterisk),
                                    ('weight', 1, label),
                                    ('fixed', 2, colon),
                                    ('weight', 10, field)])

        return urwid.Padding(editwidget, ('fixed left', 3), ('fixed right', 3))


    def pressed_ok(self, button):
        raise NotImplementedError()

    def pressed_cancel(self, button):
        raise NotImplementedError()

    def get_buttons(self):
        """ renders the ok and cancel buttons.  Called from get_body() """
        okbutton = urwid.Button('  OK', on_press=self.pressed_ok)
        cancelbutton = urwid.Button('Cancel', on_press=self.pressed_cancel)
        return urwid.GridFlow([okbutton, cancelbutton], 10, 7, 1, 'left')

    def get_header(self):
        """ the header of our form, called from main() """
        text_header = ("'paster create' Configuration"
            " - Use arrow keys to select a field to edit, select 'OK'"
            " when finished, or press ESC/select 'Cancel' to exit")
        return urwid.Text(text_header)


    def get_fields(self):
        return []

    def get_body(self):
        """ the body of our form, called from main() """
        # build the list of field widgets
        fieldset = self.get_fields()
        fieldwidgets = []
        for (label, inputname, fieldtype) in fieldset:
            fieldwidgets.append(self.get_field(label, inputname, fieldtype, self.fieldmgr))

        fieldwidgets.append(self.get_buttons())

        # SimpleListWalker provides simple linear navigation between the widgets
        listwalker = urwid.SimpleListWalker(fieldwidgets)

        # ListBox is a scrollable frame around a list of elements
        #return urwid.ListBox(listwalker, height=(''))
        return urwid.Pile(fieldwidgets)

class RegisterForm(UrwidForm):
    def get_fields(self):
        return [
            ('Username', 'username', 'text'),
            ('Password', 'password', 'text'),
            ('Emailisreallylonglabel here', 'email', 'text'),
        ]

    def pressed_ok(self, button):
        self.ui.set_urwid_toplevel(UrwidConsole(self.app, self.session, self))
