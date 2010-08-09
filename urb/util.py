import sys, traceback, StringIO

from twisted.python.log import msg as log

from urb.constants import MLW

def metadata(**kwargs):
    """A decorator for attaching arbitrary data to functions"""
    def decorator(f): 
        for k, v in kwargs.iteritems(): 
            setattr(f, k, v)
        return f
    return decorator

def dlog(message):
    if __debug__:
        trace = traceback.extract_stack()[-2]
        file, line, name = trace[0], trace[1], trace[2]
        log("[%s:%s \"%s\"] %s" % (file.split('/')[-1], line, name, message))
        
        
def dtrace(message):
    dlog(message)
    trace = StringIO.StringIO()
    traceback.print_exception(sys.exc_type, sys.exc_value, sys.exc_traceback, 99, trace)
    for line in trace.getvalue().split('\n'):
        dlog(line)
        
        
def render(message, player=None, target=None, move=None, damage=None, crit=None):
        return message.format(p=player, c=player.character, t=target, m=move, d=damage, cr=crit)


def word_table(items, perline, fmt=" ^"):
    lines = []
    while items:
        _items = []
        for n in range(perline):
            items, i = items[:-1], items[-1:]
            if i:
                _items.append(i[0])
        _items.reverse()
        result = ''.join('{2:{0}{1}}'.format(fmt, MLW / len(_items), i) for i in _items)
        lines.append(result)
    return lines
