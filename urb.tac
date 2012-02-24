from twisted.application import service
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import LogFile

FileLogObserver.timeFormat = ""

# initialize URB Application
from urb import app, irc, telnet
from urb.web import twresource

myApp = app.ApplicationClass()

application = service.Application("URB")

# add services to application
myApp.application = application
myApp.add_service(telnet.TelnetService)
myApp.add_service(twresource.DjangoService)

