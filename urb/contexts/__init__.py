from urb import imports

class Context():
    def __init__(_self, self):
        pass
    def enter(_self, self):
        pass
    def on_enter(_self, self):
        pass
    def leave(_self, self):
        pass
    def on_leave(_self, self):
        pass
    
    def on_input(_self, self, command, args):
        pass
    
    def get_commands(_self):
        attrs = dir(_self)
        ctxcmds = {}
        for attr in attrs:
            if attr.startswith("com_"):
                ctxcmds[attr[4:]] = getattr(_self, attr)
        return ctxcmds
                                                                              
def refresh( context_name ):
    return imports.refresh(context_name)

def get( context_name ):
    return imports.get('contexts', context_name)
