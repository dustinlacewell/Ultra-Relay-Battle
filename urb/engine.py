import random                   # choice

from twisted.internet.task import LoopingCall

from urb import commands, gametypes, validation
#from urb.gametypes import GameType, FFAGameType
from urb.player import Player, Session
from urb.util import dlog, dtrace


class GameEngine(object):
    motd = """
Welcome to Ultra Relay Battle :

You have succesfully logged in as %s. 
There are currently %d other players online.
If you need help getting started feel free to visit the URB website at
http://ldlework.com/wiki/urb . The main channel #urb is also good for asking
questions and getting to know people. You can see what commands are available
to you at any time by issuing the 'help' command.

If you're interested in helping the development of URB please write to:

                     dlacewell@gmail.com
    
Have fun!"""


    def __init__(self, app):
        self.app = app
        self.db = app.database
        
        self.players = {}
        self.fighters = {}
        self.next_team_id = 0
        
        self.gametime = 0
        self.tickrate = 1.0
        self.tick_timer = LoopingCall(self.tick)
        self.actions = []
        
        self.state = "idle" # idle, selection prebattle battle
        self.gametype = gametypes.get('survivor')(self)
        
    def _get_settings(self):
        return self.app.database.get_gametype(self.gametype.name)
    settings = property(_get_settings)
            
    def is_paused(self):
        return not self.tick_timer.running
        
    def is_ready(self, nickname):
        return self.fighters[nickname].ready
        
    def is_enemy(self, nickname, targetname):
        theplayer = self.fighters[nickname]
        thetarget = self.fighters[targetname]
        return not theplayer.team == thetarget.team
        
    def get_target(self, nickname, ttype):
        theplayer = self.fighters[nickname]
        if ttype == 'ally':
            allies = self.get_allies(nickname)
            return random.choice(allies)
        elif ttype == 'enemy':
            enemies = self.get_enemies(nickname)
            if len(enemies):
                return random.choice(enemies)
            else:
                return None
        elif ttype == 'self':
            return theplayer
            
    def validate_target(self, nickname, targetname, move):
        return self.gametype.validate_target(self, nickname, targetname, move)
            
    def get_ready(self):
        ready = []
        for nick, theplayer in self.fighters.iteritems():
            if theplayer.ready == True:
                ready.append(theplayer)
        return ready
        
    def get_unready(self):
        unready = []
        for nick, theplayer in self.fighters.iteritems():
            if theplayer.ready == False:
                unready.append(theplayer)
        return unready
        
    def get_team(self, id):
        theteam = []
        for nick, theplayer in self.fighters.iteritems():
            if theplayer.team == id:
                theteam.append(theplayer)
        return theteam
        
    def get_allies(self, nickname):
        theplayer = self.fighters[nickname]
        theteam = self.get_team(theplayer.team)
        theteam.remove(theplayer)
        return theteam
        
    def get_enemies(self, nickname):
        theplayer = self.fighters[nickname]
        enemies = []
        for nick, otherplayer in self.fighters.iteritems():
            if otherplayer.team != theplayer.team:
                enemies.append(otherplayer)
        return enemies
                
    def parse_message(self, nickname, message, target=None):
        theplayer = self.players[nickname]
        if "%NIK" in message:
            message = message.replace("%NIK", nickname)
        if "%CHR" in message and theplayer.character:
            message = message.replace("%CHR",  theplayer.character.fullname)
        if "%TGT" in message and target:
            message = message.replace("%TGT", target)
        return message
        
    # ENGINE EVENT HANDLERS #
    def get_signal_matrix(self):
        return {
            # Engine handlers
            'login' : self.on_login,
            'logout' : self.on_logout,
            'command' : self.on_command,
            'choose' : self.on_choose,
            'signup' : self.on_signup,
            'forfeit' : self.on_forfeit,
            'ready' : self.on_ready,
            'open_selection' : self.on_open_selection,
            # Game-type handlers
            'close_selection' : self.on_close_selection,
            'battle_start' : self.on_battle_start,
            'battle_pause' : self.on_battle_pause,
            'battle_resume' : self.on_battle_resume,
            'battle_abort' : self.on_battle_abort,
            'battle_finish' : self.on_battle_finish,
            'battle_damage' : self.on_battle_damage,
            
            
        }
    
    def on_login(self, nickname):
        session = Session(nickname, self.app)
        # Create the player object with the session
        newplayer = Player(nickname, session, self.app)
        if nickname in self.players:
            oldsession = self.players[nickname].session
            newplayer.session = oldsession
            self.players[nickname] = newplayer
            if nickname in self.fighters:
                self.fighters[nickname] = newplayer
        else:
            self.players[nickname] = newplayer
        player_count = len(self.players)
        motd = self.motd % (nickname, player_count)
        for line in motd.split("\n"):
            self.app.tell(nickname, line)
        session.switch('mainmenu') 
        
    def on_logout(self, nickname):
        if nickname in self.players:
            del self.players[nickname]
        if nickname in self.fighters:
            self.on_forfeit(nickname)
        
    def on_signup(self, nickname):
        if nickname in self.players:
            theplayer = self.players[nickname]
            self.fighters[nickname] = theplayer
            
            self.gametype.on_prep_player(self, nickname)
            
    def on_forfeit(self, nickname):
        if nickname in self.fighters:
            self.fighters[nickname].session.switch('mainmenu')
            del self.fighters[nickname]
        
    def on_choose(self, nickname, selector):
        if nickname in self.fighters:
            theplayer = self.fighters[nickname]
            char = self.app.database.get_character(selector)
            if char:
                theplayer.character = char
                join_msg = self.parse_message(nickname, char.selection_msg)
                self.app.signals['game_msg'].emit(join_msg)  
                
    def on_ready(self, nickname):
        theplayer = self.app.game.fighters[nickname]
        if theplayer.character:
            if theplayer.ready:
                theplayer.current_move = "unready"
                self.app.signals['game_msg'].emit("# ! - %s is no longer ready!" % nickname)
                self.app.tell(nickname,
                "You are no longer ready for battle.")
            else:
                theplayer.current_move = None
                self.app.tell(nickname,
                "You are now ready for battle.")
                if len(self.get_ready()) == len(self.fighters):
                    self.app.signals['game_msg'].emit("## All players are READY! ##")
        else:
            self.app.tell(nickname,
            "You cannot 'ready' until you 'pick' a character.")
            self.app.tell(nickname,
            "Use 'chars' to get a list of available characters.")
            
    def on_command(self, nickname, command, args):
        # grab the player from the roster
        theplayer = self.players[nickname]
        # Let context handle input if it wants
        session = theplayer.session
        if theplayer.session.context.on_input(session, command, args):
            return
        # determine the usable commands for this player
        allowed = commands.get_allowed(theplayer, all=True)
        if command in allowed: # only respond to allowed commands
            # format for context based commands
            contextual = "com_%s" % command
            # session contextual command
            if hasattr(theplayer.session.context, contextual):
                # get the command
                contextual = getattr(theplayer.session.context, contextual)
                # validate passed arguments against schema
                try: 
                    data = validation.command(self.app, contextual, args)
                    # run the comand if validated
                    contextual(theplayer.session, data)
                except validation.ValidationError, e:
                    self.app.tell(nickname, e.message)
                except Exception, e:
                      self.app.tell(nickname, 
                      "Sorry, that command resulted in an error on the server.")                      
                      dtrace("Context command caused an error : %s %s" % (command, args))
            else: # its not contextual so check dynamic commands
                comm_cls = commands.get(command)
                if comm_cls:
                    # validate passed arguments against schema
                    try: 
                        data = validation.command(self.app, comm_cls, args)
                        # create live command object
                        new_comm = comm_cls(self.app, theplayer, data)
                        # let command verify submission
                        new_comm.verify()
                        # If no delay, perform instantly
                        if new_comm.tick_delay == None:
                            new_comm.perform()
                            return
                    except validation.ValidationError, e:
                        self.app.tell(nickname, e.message)
                    except Exception, e:
                        self.app.tell(nickname, 
                        "Sorry, that command resulted in an error on the server.")
                        dtrace("Dynamic command caused an error : %s %s" % (command, args))
                    else: # command is good to go
                        # Otherwise send command to queue            
                        do_time = self.gametime + new_comm.tick_delay
                        self.actions.append( (do_time, new_comm) )
                else: # Inform the user the command isn't available
                    self.app.tell(nickname, "'%s' isn't an available command." % command)
        else: # Inform the user the command isn't available
            self.app.tell(nickname, "'%s' isn't an available command." % command)
    
    def on_open_selection(self, gametype):
        if self.state == "idle":
            self.fighters = {}
            self.state = "selection"
            self.gametype = gametype(self)
            self.app.signals['global_msg'].emit(
            "# Character Selection is now open for: %s." % gametype.name)
        elif self.state == "prebattle":
            self.state = "selection"
            self.app.signals['global_msg'].emit(
            "# ! Battle delayed ---------------")
            self.app.signals['global_msg'].emit(
            "# Character Selection is now open for: %s." % self.gametype.name)
        
    # GAMETYPE HANDLERS #    #    #        
    def on_close_selection(self):
        self.gametype.on_close_selection(self)
        
    def on_battle_start(self):
        self.gametype.on_battle_start(self)
        
    def on_battle_pause(self):
        self.gametype.on_battle_pause(self)
        
    def on_battle_resume(self):
        self.gametype.on_battle_pause(self)
        
    def on_battle_abort(self):
        self.gametype.on_battle_abort(self)
        
    def on_battle_finish(self, winid):
        self.gametype.on_battle_finish(self, winid)
        
    def on_battle_damage(self, nickname, targetname, damage):
        self.gametype.on_battle_damage(self, nickname, targetname, damage)
    
    def tick(self):
        for fighter in self.fighters.values():
            fighter.magicpoints = min(self.settings.maxmagic, fighter.magicpoints + self.settings.mprate)
        winid = self.gametype.check_win_condition(self)
        if winid != None:
            self.app.signals['battle_finish'].emit(winid)
        self.gametime += 1
        if self.actions:
            for action in list(self.actions):
                if action[0] <= self.gametime:
                    if action[1].alive:
                        action[1].alive = False
                        action[1].perform()
                if not action[1].alive:
                    self.actions.remove(action)
                        
    def start_battle_timers(self):
        self.tick_timer.start(self.tickrate)
    
    def stop_battle_timers(self):
        self.tick_timer.stop()
