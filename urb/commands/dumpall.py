from urb import commands, imports
from urb.colors import colorize
from urb.util import dlog, metadata

class DumpAllCommand(commands.Command):
    """
Takes a filename parameter and proceeds to dump all commands including
their help information and schema lines.
"""
    adminlevel = commands.ADMIN
    schema = ( ('str','filename'), )
    
    def perform(self):
        fobj = open(self.args['filename'], 'w')
        allcomobj = imports.load_all('commands')
        print allcomobj
        for name, comobj in allcomobj.iteritems():
            lines = [line + "\n" for line in commands.get_help(comobj)]
            fobj.writelines(lines)
                
            fobj.write("-"*79 + "\n")
        fobj.close()
        self.app.tell(self.player.nickname, 
        "%d commands dumped to %s" % (len(allcomobj), self.args['filename']))

exported_class = DumpAllCommand
