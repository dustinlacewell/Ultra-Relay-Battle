from twisted.internet import reactor

from urb.players.models import Player
from urb.constants import COUNTDOWN
from urb.gametypes.models import GameRecord, GameType
from urb.gametypes import get
from urb.gametypes.survivor import Survivor

class GameManager(dict):
    def __init__(self, app):
        self.app = app

    def get_records(self):
        return GameRecord.objects.filter(
            state__notin=[
                'finished', 'aborted',
            ]
        )
    records = property(get_records)

    def get_players(self):
        return Player.objects.filter(
            game__isnull=False,
        )
    players = property(get_players)

    def create_game(self, gametype=None):
        # create game record
        record = GameRecord.objects.create()
        engine_cls = Survivor
        if gametype:
            # get gametype
            record.gametype = GameType.objects.get(selector=gametype)
            record.save()
            engine_cls = get(record.gametype.engine)
        engine = engine_cls(self.app, record.id)
        # register game
        self[record.id] = engine
        return self[record.id]

    def register_player(self, gid, pid):
        player = Player.objects.get(id=pid)
        record = GameRecord.objects.get(id=gid)
        player.game = record
        player.save()
        return player

    def start_game(self, gid):
        game = self[gid]
        game.countdown = COUNTDOWN
        record = game.record
        record.state = 'prebattle'
        record.save()
        reactor.callLater(1.0, self.countdown, (gid,))

    def countdown(self, gid):
        game = self[gid]

        if game.record.state == 'selection':
            return

        game.countdown -= 1
        if game.countdown == 0:
            reactor.callLater(game.record.tickrate, self.tick, (gid,))
        else:
            reactor.callLater(1.0, self.countdown, (gid,))

    def tick(self, gid):
        game = self[gid]
        game.tick()
        if record.state == 'battle':
            reactor.callLater(record.tickrate, self.tick, (gid,))
