from axiom.attributes import *

from urb import contexts, db, commands, validation
from urb.colors import colorize
from urb.util import dlog, metadata
from urb.constants import *

class AdminContext(contexts.Context):
    """
ADMIN MODE    
 
The ADMIN MODE is available for the administration of user accounts.
 
"""

    def enter(_self, self):
        self.cmd(self.player, 'help', [])  
            
        _self.working = None
            
    def _to_dict(_self, listobj):
        newdict = {}
        for key, val in listobj:
            newdict[key] = val
        return newdict

    def com_exit(_self, self, args):
        "Exit to the main-menu."
        self.revert()
    
    @metadata(schema=(('user','nickname'), ('str','password')))
    def com_setpass(_self, self, args):
        """
Print gametype settings. Passing no filters prints all 
settings or The filters are a list of settings to print. The filters you 
pass in can be partial and will print any settings that they match. Passing 
'max' would return all the max settings, for example. 
"""
        user = args['nickname']
        newpass =  args['password']
        user.password = newpass
        if user.password == newpass:
            self.msg("{u.nickname}'s password has been set to '{u.password}'.".format(u=user))

    @metadata(schema=(('user', 'nickname'),))
    def com_rm(_self, self, args):
        """
Remove a user account permanently from the system.
"""
        user = args['nickname']
        nick = user.nickname
        user.delete()
        self.msg("{u.nickname} has been permanently deleted.".format(u=user))
            
                        
exported_class = AdminContext
