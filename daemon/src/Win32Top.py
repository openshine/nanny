#!/usr/bin/env python

# Copyright (C) 2009,2010 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
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
import time
import win32com.client
import wmi
import gobject
from twisted.internet import reactor
import copy

class Win32Top(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.process_list = {}
        self.first_time = True
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

    def start(self):
        print "Start Win32 Top"
        gobject.timeout_add(1000, self.__update_info)

    def stop(self):
        print "Stop Win32 Top"

    def __update_info(self):
        if self.first_time == True:
            print "[W32TOP] Initial process check start"

        oWMI = win32com.client.GetObject(r"winmgmts:\\.\root\cimv2")
        qry = "SELECT * FROM Win32_Process"
        qry = oWMI.ExecQuery(qry)
        users_list = self.quarterback.usersmanager.get_users()

        if qry.count > 0:
            pids_list = []
            for result in qry:
                pid = int(result.ProcessId)
                pids_list.append(pid)
                name = unicode(result.Name)
                cdate = unicode(result.CreationDate)
                
                if pid not in self.process_list :
                    try:               
                        w = wmi.WMI()
                        p = w.Win32_Process(ProcessID=pid)
                        uid_name = p[0].GetOwner()[2]
                        uid_number = None
                        for uid, uname, ufname in users_list:
                            if uname == uid_name :
                                uid_number = uid
                                break
                        if uid_number == None :
                            uid_number = 0
                    except:
                        uid_number = 0
                    
                    self.process_list[pid] = [uid_number, name, cdate]
                    if self.first_time == False:
                        print "[W32TOP] Add process (%s) : [uid: %s, name: '%s']" % (pid, uid_number, name)
                else:
                    u, n, c = self.process_list[pid]
                    if c != cdate:
                        try:
                            uid_name = wmi.WMI().Win32_Process(ProcessID=pid).GetOwner()[0]
                            uid_number = None
                            for uid, uname, ufname in users_list:
                                if uname == uid_name :
                                    uid_number = uid
                                    break
                            if uid_number == None :
                                uid_number = 0
                        except:
                            uid_number = 0

                        self.process_list[pid] = [uid_number, name, cdate]
                        if self.first_time == False:
                            print "[W32TOP] Add process (%s) : [uid: %s, name: '%s']" % (pid, uid_number, name)
                
            new_process_list = copy.copy(self.process_list)
            for pid in self.process_list :
                if pid not in pids_list :
                    uid_number, name, cdate = self.process_list[pid]
                    if self.first_time == False:
                        print "[W32TOP] Remove process (%s) : [uid: %s, name: '%s']" % (pid, uid_number, name)
                    new_process_list.pop(pid)
            self.process_list = new_process_list
            
            if self.first_time == True:
                self.first_time = False
                print "[W32TOP] Initial process check finished"
            return True

                    
                
            
        
        
