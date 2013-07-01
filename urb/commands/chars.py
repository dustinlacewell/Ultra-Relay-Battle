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
                for move in self.args['mselector']:
                    if move.ownerselector == cselector:
                        themove = move
                if themove:
                    mselector = move.selector
                    self.session.msg(themove.info)
                else:
                    self.session.msg("'%s' doesn't have that move." %(cselector, ))
            else:
                moves = char.moves
                self.session.msg("%s (%s)" % (char.fullname, char.selector))
                self.session.msg("Physical Str: %s" % char.get_gauge('pstrength'))
                self.session.msg("Physical Def: %s" % char.get_gauge('pdefense'))
                self.session.msg("Magical Str:  %s" % char.get_gauge('mstrength'))
                self.session.msg("Magical Def:  %s" % char.get_gauge('mdefense'))
                if char.weakness != 'none': 
                    self.session.msg("Is weak to %s effects" % char.weakness)
                if char.resistance != 'none': 
                    self.session.msg("Is resistant to %s effects" % char.resistance)
                self.session.msg("-- Moves " + ("-" * 32))
                for move in moves:
                    mselector = move.selector
                    self.session.msg( move.info)
        else:
            chars = [ char.selector for char in Character.all() if char.finalized != 0]
            unfinished = [ char.selector for char in Character.all() if char.finalized == 0]
            self.session.msg("Ultra Relay Battle - Character listing :")
            send = ""
            for char in chars:
                oldsend = send
                send = "%s%s " % (send, ("'%s' " % char))
                if len(send) >= 255:
                    self.session.msg(oldsend)
                    send = ("%s " % char)
                elif len(send) >= 245:
                    self.session.msg(send)
                    send = ""
            if unfinished and self.player.session.context_name == 'builder':
                send += "\nUnfinished: %s" % (", ".join(unfinished))
            if send:
                self.session.msg(send)
             
exported_class = CharsCommand
