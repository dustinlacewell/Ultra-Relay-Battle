from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class InfoCommand(commands.Command):
    """
Get information on a chararcter or character move.
"""

    adminlevel = commands.PLAYER
    schema = (
        ('char','cselector'),
        ('move*','mselector'),
    )
    def perform(self):
        char = self.args['cselector']
        move = None
        if 'mselector' in self.args:
            moves = self.args['mselector']
            charmoves = self.app.database.get_moves_for(char.selector)
            for move in moves:
                for charmove in charmoves:
                    if charmove.selector.startswith(move.selector):
                        move = charmove
            if move:
                self.app.tell(self.player.nickname,
                "%s : %d : %s : %s" % (
                move.fullname, move.power,
                move.element, move.target))
            else:
                self.app.tell(self.player.nickname,
                "'%s' doesn't have that move." % char.selector)
        else:
            self.app.tell(self.player.nickname,
            "%s (%s):" % (char.fullname, char.selector))
            self.app.tell(self.player.nickname,
            "Physical Str/Def:  %d/%d" % (char.pstrength, char.pdefense))
            self.app.tell(self.player.nickname,
            "Magical Str/Def:   %d/%d" % (char.mstrength, char.mdefense))
            self.app.tell(self.player.nickname,
            "Elemental Str/Def: %s/%s" % (char.resistance, char.weakness))
            self.app.tell(self.player.nickname, char.description_msg)
             
exported_class = InfoCommand
