from urb import commands
from urb.colors import colorize
from urb.util import dlog, metadata

class NewGameCommand(commands.Command):
    """
Create a new game lobby.
"""

    adminlevel = commands.MODERATOR
    schema=(('gametype*','gametype'),)
    def perform(self):
        new_game = self.app.games.create_game(self.args.get('gametype', None))

        if 'gameslug' in self.args:
            lcall, engine = self.args['gameslug']
            if self.player in engine.record.players:
                self.session.msg("You're already a participant in battle.")
            elif engine.state == 'selection':
                if 'cselector' in self.args and self.args['cselector'].finalized == 0:
                    self.session.msg("'%s' is not a valid character selector." % self.args['selector'].selector)
                else:
                    self.app.games.register_player(engine.record_id, self.session.pid, self.args['cselector'] if self.args else None)
            else:
                self.session.msg("Character selection isn't currently open right now.")
        else:
            if len(self.app.games):
                self.session.msg("Currently available games:")
                for gid, gameinfo in self.app.games.items():
                    lcall, engine = gameinfo
                    msg = "%s\t- %s\t- %s players"
                    msg = msg % (gid, engine.record.state, engine.players.count())
                    self.session.msg(msg)
            else:
                self.session.msg("There are no available games.")
exported_class = FightCommand
