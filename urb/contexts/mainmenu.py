from urb import contexts, commands
from urb.players.models import Player
from urb.colors import colorize
from urb.util import dlog, metadata, word_table

class MainMenuContext(contexts.Context):
    """MAIN MENU"""
    allowed = ['minigames']
    
    def enter(_self, self):
        _self.app = self.app
        self.cmd('help', [])   

    def __get_doc(self):
        header = "THE LOBBY\n\n  The following users are here:\n\n"
        nlist = list(Player.objects.filter(game__isnull=True))
        table = '\n'.join(word_table(nlist, 4))
        return header + table
    __doc__ = property(__get_doc)

exported_class = MainMenuContext
