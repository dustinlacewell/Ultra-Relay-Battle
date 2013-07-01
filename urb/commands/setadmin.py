from django.contrib.auth.models import Group

from urb import commands
from urb.util import dlog

class SetAdminCommand(commands.Command):
    """
Set the administration level for a particular user.
"""

    adminlevel = commands.ADMIN
    schema = (('player','username'), ('int','adminlevel'))
    
    def perform(self):
        player = self.args['username']
        player.groups.add(Group.objects.get(name=self.args['adminlevel']))
        self.session.msg("%s's adminlevel now set to %d" % (player.username, self.args['adminlevel']))

exported_class = SetAdminCommand
