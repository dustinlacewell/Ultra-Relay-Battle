import math, random

MOTD = """
Welcome to Ultra Relay Battle :
 
You have succesfully logged in as %s. 
There are currently %d other players online.
If you need help getting started feel free to visit the URB website at \
http://ldlework.com/wiki/urb . The main channel #urb is also good for \
asking questions and getting to know people. 

You can see what commands are available to you at any time by issuing the 'help' command.

If you're interested in helping the development of URB please write to: 

dlacewell@gmail.com

Have fun!"""
MLW = 78
#
# Character Creation
# 
MIN_CHAR_STAT = 25
MAX_CHAR_STAT = 100

MAX_CHAR_STAT_TOTAL = 250

WEAKNESS_STAT_DELTA = 50
RESISTANCE_STAT_DELTA = -25

MAX_MOVE_POWER = 100

#
# Damage Calculation
#
BFACTOR = 1.09
LOW_END_FRACTION = 1/32.0
HIGH_END_FRACTION = 1/8.0
CRITICAL_POWER_FACTOR = 1.5
def f(x):
   return (x-float(MIN_CHAR_STAT - 1.0)) ** BFACTOR + float(MIN_CHAR_STAT - 1.0)

L_MIN = math.log( float(MIN_CHAR_STAT) / f(float(MAX_CHAR_STAT)) )
L_MAX = math.log( float(MAX_CHAR_STAT) / f(float(MIN_CHAR_STAT)) )

def challenge_factor(st, df):
    return (math.log( st / f(df) ) - L_MIN ) * 1.2 / (L_MAX - L_MIN) + 0.8

def calculate_damage(attack, defense, power, maxhp):
    base = maxhp * ( HIGH_END_FRACTION*(power/float(MAX_MOVE_POWER)) + LOW_END_FRACTION*(1-(power/float(MAX_MOVE_POWER))) ) 
    multi = challenge_factor(attack, defense)
    return base * multi

def is_critical(st, df):
    chance = challenge_factor(st, df) * 10
    return (random.random() * 100) <= chance 


#
# Elements
#
elements = ['physical', 'heal', 'hpdrain', 'spdrain', 'reveal', 'demi']

MAX_DEMI_RATIO = 0.95