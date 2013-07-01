from urb.gametypes.engine import GameEngine

class Survivor(GameEngine):
    name = "survivor"

    def on_battle_finish(self, winid):
        team = self.get_team(winid)
        winner = team[0]
        self.app.fsay(" ! BATTLE IS OVER ! ", fmt="*^")
        self.app.fsay("%s is the sole survivor!" % winner.nickname)
        self.state = "idle"
        self.tick_timer.stop()
        for nick, theplayer in list(self.fighters.iteritems()):
            self.player_forfeit(theplayer)
        self.actions = []
        
        
    def check_win_condition(self):
        alive = []
        for nickname, theplayer in self.fighters.iteritems():
            if theplayer.health > 0:
                alive.append(theplayer)
        if len(alive) == 1:
            self.finish_battle(alive[0].team)
            return True


        
exported_class = Survivor
