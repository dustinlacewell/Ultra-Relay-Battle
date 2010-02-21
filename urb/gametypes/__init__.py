from urb import imports

from urb.util import dlog, dtrace
from urb import validation
from urb.validation import ValidationError

class GameType(object):
    def __init__(_self, self):
        pass
    def on_setup(_self, self):
        pass
    
    def on_prep_player(_self, self, nickname):
        if nickname in self.fighters:
            theplayer = self.fighters[nickname]
            theplayer.character = None
            theplayer.current_move = None
            theplayer.ready = False
            theplayer.health = self.settings.starthealth
            theplayer.magicpoints = self.settings.startmagic
            theplayer.team = self.next_team_id
            self.next_team_id += 1
            
            theplayer.session.switch('prebattle')    
            
    def on_close_selection(_self, self):
        if self.state == "selection":
            for nick, theplayer in self.fighters.iteritems():
                readystr = 'READY' if theplayer.ready else '*NOT-READY*'
                if theplayer.character:
                    self.app.signals['game_msg'].emit(
                    "# %s(%s) - %d HP - %s" % (
                    nick, theplayer.character.fullname,  theplayer.health, readystr))
                else:
                    self.app.signals['game_msg'].emit(
                    "%s(NO CHAR) - %d HP - %s" % (
                    nick, theplayer.health, readystr))
            if len(self.get_ready()) == len(self.fighters):
                self.app.signals['global_msg'].emit(
                "# Character Selection is now closed.")
                self.state = "prebattle"
            else:
                self.app.signals['game_msg'].emit(
                "##    Waiting for all players to READY.   ##")
                unready = self.get_unready()
                for theplayer in unready:
                    self.app.tell(theplayer.nickname,
                        "!! Battle is waiting on you to, 'ready' !!")
            
                        
    def on_battle_start(_self, self):
        if self.state == "prebattle":
            unready = self.get_unready()
            for theplayer in unready:
                nickname = theplayer.nickname
                self.app.signals['game_msg'].emit(
                "%s was dropped from the battle." % nickname)
                self.on_forfeit(nickname)
                self.app.tell(nickname,
                "You were dropped from battle for not being ready.")
            for nickname, theplayer in self.fighters.iteritems():
                theplayer.session.switch('battle')
            self.app.signals['game_msg'].emit(
            "****  BATTLE HAS BEGUN ****")
            self.tick_timer.start(self.tickrate)
        
    def on_battle_pause(_self, self):
        pass
        
    def on_battle_resume(_self, self):
        pass
        
    def on_battle_abort(_self, self):
        self.tick_timer.stop()
        self.actions = []
        self.app.signals['game_msg'].emit(
        "**** BATTLE HAS BEEN ABORTED ****")
        for nick, theplayer in list(self.fighters.iteritems()):
            self.on_forfeit(nick)
            self.app.tell(nick,
            "**** BATTLE HAS BEEN ABORTED ****")
                 
    def on_battle_finish(_self, self, winid):
        pass
        
    def on_battle_damage(_self, self, nickname, targetname, damage):
        theplayer = self.fighters[nickname]
        thetarget = self.fighters[targetname]
        thetarget.health -= damage
        thetarget.health = min(self.app.game.settings.maxhealth, thetarget.health)
        hit_msg = self.app.game.parse_message(nickname, theplayer.current_move.move.hit_msg, targetname)
        hit_msg = "%s [%d]" % (hit_msg, abs(damage))
        self.app.signals['game_msg'].emit(hit_msg)
        if thetarget.health <= 0:
            death_msg = self.parse_message(nickname, thetarget.character.death_msg, targetname)
            self.app.signals['game_msg'].emit(death_msg)
            self.app.signals['game_msg'].emit(
            "Death slaps a sticker on %s, \"Kaput!\", you're dead. [%d]" % (
            thetarget.nickname, thetarget.health))
        theplayer.current_move = None
        theplayer.ready = True
        winid = _self.check_win_condition(self)
        if winid != None:
            self.app.signals['battle_finish'].emit(winid)
        elif self.is_ready(nickname):
            self.app.signals['game_msg'].emit(theplayer.status_msg)
        
        
    def on_defect(_self, self):
        pass
        
    def is_ready(_self, self, nickname):
        theplayer = self.fighters[nickname]
        if not theplayer.current_move:
            return True
            
    def validate_target(_self, self, nickname, targetname, move):
        ttype = move.target
        target = None
        
        if not targetname and ttype in ['ally', 'enemy']:
            raise ValidationError( 
            "The '%s' move requires a target. (%s)" % (move.fullname, ttype))
        elif not targetname and ttype in ['self', 'ally-all', 'enemy-all']:
            return True
        elif targetname and ttype in ['ally', 'enemy']:
            target, left = validation.fighter(self.app, nickname, [targetname])    

            if ttype == "ally":
                if self.is_enemy(nickname, targetname):
                    raise ValidationError(
                    "'%s' can only target allies." % (move.fullname))
                elif self.fighters[targetname].health <= 0:
                    raise ValidationError(
                    "%s is dead man. They're dead." % targetname)
                else:
                    return True
            elif ttype == "enemy":
                if not self.is_enemy(nickname, targetname):
                    raise ValidationError(
                    "%s' can only target enemies." % (move.fullname))
                elif self.fighters[targetname].health <= 0:
                    raise ValidationError(
                    "%s is already dead. What good would that do?" % targetname)
                else:
                    return True
                                                                              
def refresh( gametype_name ):
    return imports.refresh(gametype_name)

def get( gametype_name ):
    return imports.get('gametypes', gametype_name)
