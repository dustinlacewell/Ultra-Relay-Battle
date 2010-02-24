from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class CharsCommand(commands.Command):
    """
Get information on a chararcter or character move.
"""

    adminlevel = commands.PLAYER
    schema = (('char*','cselector'), ('move*','mselector'))
    def perform(self):
        if 'cselector' in self.args and self.args['cselector'].finalized != 0:
            char = self.args['cselector']
            cselector = char.selector
            if 'mselector' in self.args:
                move = self.args['mselector']
                mselector = move.selector
                self.app.tell(self.player.nickname, 
                    "%s - %d : %s : %s - CanSpr: %d, CanCtr: %d" % (
                    move.fullname, move.element, move.target, move.cansuper, move.cancounter))
            else:
                moves = self.app.database.get_moves_for(cselector)
                self.app.tell(self.player.nickname,
                    "%s (%s)" % (char.fullname, char.selector))
                self.app.tell(self.player.nickname,
                    "Physical: %d / %d" % (char.pstrength, char.pdefense))
                self.app.tell(self.player.nickname,
                    "Magical: %d / %d" % (char.mstrength, char.mdefense))
                self.app.tell(self.player.nickname, "Weakness: %s" % char.weakness)
                self.app.tell(self.player.nickname, "Resistance: %s" % char.resistance)
                for move in moves:
                    mselector = move.selector
                    self.app.tell(self.player.nickname, 
                    "%s - %d : %s : %s - CanSpr: %d, CanCtr: %d" % (
                    move.fullname, move.element, move.target, move.cansuper, move.cancounter))
        else:
            chars = [ char.selector for char in self.app.database.get_all_characters() if char.finalized != 0]
            unfinished = [ char.selector for char in self.app.database.get_all_characters() if char.finalized == 0]
            self.app.tell(self.player.nickname,
            "Ultra Relay Battle - Character listing :")
            send = ""
            for char in chars:
                oldsend = send
                send = "%s%s " % (send, ("'%s' " % char))
                if len(send) >= 255:
                    self.app.tell(self.player.nickname, oldsend)
                    send = ("%s " % char)
                elif len(send) >= 245:
                    self.app.tell(self.player.nickname, send)
                    send = ""
            if unfinished and self.player.session.context_name == 'builder':
                send += "\nUnfinished: %s" % (", ".join(unfinished))
            if send:
                self.app.tell(self.player.nickname, send)
             
exported_class = CharsCommand
