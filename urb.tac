# -*- python -*-
import sys
sys.path.append('.')

from twisted.application import service
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import LogFile

from urb import app, irc, telnet
myApp = app.ApplicationClass()

FileLogObserver.timeFormat = ""

application = service.Application("URB")
myApp.application = application
myApp.add_service(telnet.TelnetService)
myApp.add_service(irc.IRCService )
