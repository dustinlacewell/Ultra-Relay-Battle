from urb.gametypes import GameType

class Survivor(GameType):
    name = "survivor"

    def on_battle_finish(_self, self, winid):
        team = self.get_team(winid)
        winner = team[0]
        self.app.signals['game_msg'].emit(
        "****  ! BATTLE IS OVER !  ****")
        self.app.signals['game_msg'].emit(
        "%s is the sole survivor!" % winner.nickname)
        self.state = "idle"
        self.tick_timer.stop()
        for nick, theplayer in list(self.fighters.iteritems()):
            self.on_forfeit(nick)
        self.actions = []
        
    def check_win_condition(_self, self):
        alive = []
        for nickname, theplayer in self.fighters.iteritems():
            if theplayer.health > 0:
                alive.append(theplayer)
        if len(alive) == 1:
            return alive[0].team
        
exported_class = Survivor