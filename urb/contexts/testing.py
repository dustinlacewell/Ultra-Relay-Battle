from urb import contexts
from urb.colors import colorize
from urb.util import dlog, metadata

__test__ = False                # need this to make nose happy


class TestingContext(contexts.Context):
    """
This context is used for testing various features of the internal features of
the game. Its behavior is undefined. Check the source if you are unsure.
"""
        
    def com_exit(_self, self, args):
        """Exit back to the main-menu."""
        self.switch('mainmenu')         
    
    def com_test(_self, self, args):
        pass
           

exported_class = TestingContext
