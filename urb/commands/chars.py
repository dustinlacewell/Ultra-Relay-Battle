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
                    self.player.tell(themove.info)
                else:
                    self.player.tell("'%s' doesn't have that move." %(cselector, ))
            else:
                moves = char.moves
                self.player.tell("%s (%s)" % (char.fullname, char.selector))
                self.player.tell("Physical Str: %s" % char.get_gauge('pstrength'))
                self.player.tell("Physical Def: %s" % char.get_gauge('pdefense'))
                self.player.tell("Magical Str:  %s" % char.get_gauge('mstrength'))
                self.player.tell("Magical Def:  %s" % char.get_gauge('mdefense'))
                if char.weakness != 'none': 
                    self.player.tell("Is weak to %s effects" % char.weakness)
                if char.resistance != 'none': 
                    self.player.tell("Is resistant to %s effects" % char.resistance)
                self.player.tell("-- Moves " + ("-" * 32))
                for move in moves:
                    mselector = move.selector
                    self.player.tell( move.info)
        else:
            chars = [ char.selector for char in Character.all() if char.finalized != 0]
            unfinished = [ char.selector for char in Character.all() if char.finalized == 0]
            self.player.tell("Ultra Relay Battle - Character listing :")
            send = ""
            for char in chars:
                oldsend = send
                send = "%s%s " % (send, ("'%s' " % char))
                if len(send) >= 255:
                    self.player.tell(oldsend)
                    send = ("%s " % char)
                elif len(send) >= 245:
                    self.player.tell(send)
                    send = ""
            if unfinished and self.player.session.context_name == 'builder':
                send += "\nUnfinished: %s" % (", ".join(unfinished))
            if send:
                self.player.tell(send)
             
exported_class = CharsCommand
