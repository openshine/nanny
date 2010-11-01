#!/usr/bin/env python
# Copyright (C) 2009 Roberto Majadas, Cesar Garcia, Luis de Bethencourt
# <openshine.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import os
import sys

# Reactor stuff
from twisted.application import app, service
import twisted.internet.gtk2reactor
twisted.internet.gtk2reactor.install()
from twisted.internet import reactor
reactor.suggestThreadPoolSize(30)

# W32 service stuff
import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager


#Add nanny module to python paths
if not hasattr(sys, "frozen") :
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nanny_lib_path = os.path.join(root_path, "lib", "python2.6", "site-packages")
    sys.path.append(nanny_lib_path)


def main():
    #Start UP application
    import nanny.daemon
    application = service.Application('nanny')
    daemon = nanny.daemon.Daemon(application)

    app_service = service.IService(application)
    app_service.privilegedStartService()
    app_service.startService()
    reactor.addSystemEventTrigger('before', 'shutdown',
                                  app_service.stopService)

    #Reactor Run
    if not hasattr(sys, "frozen") :
        reactor.run()
    else:
        reactor.run(installSignalHandlers=0)

class NannyService (win32serviceutil.ServiceFramework):
    _svc_name_ = "NannyService"
    _svc_display_name_ = "Nanny Daemon Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        if not os.path.exists(os.path.join(os.environ["ALLUSERSPROFILE"], "Gnome", "nanny", "nanny.log")):
            try:
                os.makedirs(os.path.dirname(os.path.join(os.environ["ALLUSERSPROFILE"], "Gnome", "nanny", "nanny.log")))
            except:
                pass

        self.log = open(os.path.join(os.environ["ALLUSERSPROFILE"], "Gnome", "nanny", "nanny.log"), "w")


    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        import servicemanager

        self.CheckForQuit()
        pythoncom.CoInitialize()

        sys.stdout = self.log
        sys.stderr = self.log
        
        #Start UP application
        import nanny.daemon
        application = service.Application('nanny')
        self.daemon = nanny.daemon.Daemon(application)
        
        app_service = service.IService(application)
        app_service.privilegedStartService()
        app_service.startService()
        reactor.addSystemEventTrigger('before', 'shutdown',
                                      app_service.stopService)
        
        #Reactor Run
        if not hasattr(sys, "frozen") :
            reactor.run()
        else:
            reactor.run(installSignalHandlers=0)

    def CheckForQuit(self):
            retval = win32event.WaitForSingleObject(self.hWaitStop, 10)
            if not retval == win32event.WAIT_TIMEOUT:
                print " Received Quit from Win32"
                self.daemon.win32_service_stop()
                reactor.stop()
                print "STOP"
                self.log.close()
                pythoncom.CoUninitialize()
                
            reactor.callLater(1.0, self.CheckForQuit)

    def main(self):
        main()


if __name__ == '__main__':
    if len(sys.argv) == 1 :
        main()
    else:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        win32serviceutil.HandleCommandLine(NannyService)
