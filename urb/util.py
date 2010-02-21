import sys, traceback, StringIO

from twisted.python.log import msg as log

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
