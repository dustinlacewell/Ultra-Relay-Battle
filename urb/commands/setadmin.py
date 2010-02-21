from urb import commands
from urb.util import dlog

class SetAdminCommand(commands.Command):
    """
Set the administration level for a particular user.
"""

    adminlevel = commands.ADMIN
    schema = (('user','nickname'), ('int','adminlevel'))
    
    def perform(self):
        user = self.args['nickname']
        user.adminlevel = self.args['adminlevel']
        self.app.tell(self.player.nickname, 
            "%s's adminlevel now set to %d" % (user.nickname, self.args['adminlevel']))
        self.alive = False

exported_class = SetAdminCommand
