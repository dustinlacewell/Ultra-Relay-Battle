class Signal(object):
    """A simple event system using direct callbacks.  

    In URB, they are exclusively fired by name on a signals dict in
    ApplicationClass, not from direct references.  This extra
    indirection plus the registration machinery that connects event
    handlers by their names causes these events to behave in a
    signal/slot fashion similar to Qt -- thus the name "Signal"
    instead of "Event"
    """
    
    def __init__(self):
        self._listeners = []
        
    def register(self, listener, prio=None):
        if listener in self._listeners:
            self.unregister(listener)
        if prio and prio < len(self._listeners):
            self._listeners.insert(prio, listener)
        else:
            self._listeners.append(listener)
        
    def unregister(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)
            
    def emit(self, *args, **kwargs):
        for listener in self._listeners:
            listener(*args, **kwargs)


    # optional C#-inspired syntax sugar

    def __len__(self):
        return len(self._listeners)

    def __iadd__(self, listener):
        self.register(listener)
        return self

    def __isub__(self, listener):
        self.unregister(listener)
        return self

    __call__ = emit



