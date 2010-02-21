import re

color_key = '\x03' 
color_map = ['white', 'black',
             'blue', 'green',
             'lightred', 'red',
             'purple', 'orange',
             'yellow', 'lightgreen',
             'cyan', 'lightcyan',
             'lightblue', 'pink',
             'grey', 'lightgrey'
            ]

def colorize(string):
    for color in color_map:
        string = re.sub('<%s>' % color,
                '%s%d' % (color_key, color_map.index(color)), string)
    return string
        

