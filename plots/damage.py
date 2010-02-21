import math, random
import matplotlib.pyplot as plt

POWERMIN = 25
POWERMAX = 100

STMIN = 25
STMAX = 100

DFMIN = 25
DFMAX = 100

MAXHP = 1000

B = 1.9

xpoint = []
ypoint = []

def f(x):
   return (x-24.0) ** B + 24.0

L_MIN = math.log( 25.0 / f(100.0) )
L_MAX = math.log(100.0 / f(25.0) )

def multi(st, df):
    return (math.log( st / f(df) ) - L_MIN ) * 1.2 / (L_MAX - L_MIN) + 0.8
    

st = 100
df = STMAX

# ITERATE STRENGTHS/DEFENSES
for df in range(25, DFMAX, 1):
    xpoints = []
    ypoints = []
    # ITERATE MOVE POWER
    for power in range(POWERMAX):
        y = MAXHP * ( (1/8.)*(power/100.0) + (1/32.)*(1-(power/100.0)) ) 
        ymul = multi(st, df)
        
        xpoints.append(power)
        ypoints.append(y* ymul)
    plt.plot(xpoints, ypoints)

plt.xlabel('Move Power')
plt.ylabel('Damage')
plt.show()


