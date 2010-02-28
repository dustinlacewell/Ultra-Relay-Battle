from urb.db import *
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
                themove = None
                mselector = None
                print [move.info for move in self.args['mselector']]
                for move in self.args['mselector']:
                    if move.ownerselector == cselector:
                        themove = move
                if themove:
                    mselector = move.selector
                    self.app.tell(self.player, themove.info)
                else:
                    self.app.tell(self.player, "'%s' doesn't have that move." %(cselector, ))
            else:
                moves = char.moves
                self.app.tell(self.player,
                    "%s (%s)" % (char.fullname, char.selector))
                self.app.tell(self.player,"Physical Str: %s" % char.get_gauge('pstrength'))
                self.app.tell(self.player,"Physical Def: %s" % char.get_gauge('pdefense'))
                self.app.tell(self.player,"Magical Str:  %s" % char.get_gauge('mstrength'))
                self.app.tell(self.player,"Magical Def:  %s" % char.get_gauge('mdefense'))
                if char.weakness != 'none': 
                    self.app.tell(self.player, "Is weak to %s effects" % char.weakness)
                if char.resistance != 'none': 
                    self.app.tell(self.player, "Is resistant to %s effects" % char.resistance)
                self.app.tell(self.player, "-- Moves " + ("-" * 32))
                for move in moves:
                    mselector = move.selector
                    self.app.tell(self.player, move.info)
        else:
            chars = [ char.selector for char in Character.all() if char.finalized != 0]
            unfinished = [ char.selector for char in Character.all() if char.finalized == 0]
            self.app.tell(self.player,
            "Ultra Relay Battle - Character listing :")
            send = ""
            for char in chars:
                oldsend = send
                send = "%s%s " % (send, ("'%s' " % char))
                if len(send) >= 255:
                    self.app.tell(self.player, oldsend)
                    send = ("%s " % char)
                elif len(send) >= 245:
                    self.app.tell(self.player, send)
                    send = ""
            if unfinished and self.player.session.context_name == 'builder':
                send += "\nUnfinished: %s" % (", ".join(unfinished))
            if send:
                self.app.tell(self.player, send)
             
exported_class = CharsCommand
