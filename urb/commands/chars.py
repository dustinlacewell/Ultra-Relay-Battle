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
                    self.app.tell(self.player.nickname, themove.info)
                else:
                    self.app.tell(self.player.nickname, "'%s' doesn't have that move." %(cselector, ))
            else:
                moves = self.app.database.get_moves_for(cselector)
                self.app.tell(self.player.nickname,
                    "%s (%s)" % (char.fullname, char.selector))
                self.app.tell(self.player.nickname,"Physical Str: %s" % char.get_gauge('pstrength'))
                self.app.tell(self.player.nickname,"Physical Def: %s" % char.get_gauge('pdefense'))
                self.app.tell(self.player.nickname,"Magical Str:  %s" % char.get_gauge('mstrength'))
                self.app.tell(self.player.nickname,"Magical Def:  %s" % char.get_gauge('mdefense'))
                if char.weakness != 'none': 
                    self.app.tell(self.player.nickname, "Is weak to %s effects" % char.weakness)
                if char.resistance != 'none': 
                    self.app.tell(self.player.nickname, "Is resistant to %s effects" % char.resistance)
                self.app.tell(self.player.nickname, "-- Moves " + ("-" * 32))
                for move in moves:
                    mselector = move.selector
                    self.app.tell(self.player.nickname, move.info)
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
