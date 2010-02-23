import math

#===============================================================================
# MIN_CHAR_PHYS_STR = 25
# MAX_CHAR_PHYS_STR = 100
# 
# MIN_CHAR_PHYS_DEF = 25
# MAX_CHAR_PHYS_DEF = 100
# 
# MIN_CHAR_MAGI_STR = 25
# MAX_CHAR_MAGI_STR = 100
# 
# MIN_CHAR_MAGI_DEF = 25
# MAX_CHAR_MAGI_DEF = 100
#===============================================================================

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