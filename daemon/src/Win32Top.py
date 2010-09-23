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
import win32api
import win32com.client
import gobject
from twisted.internet import reactor
import copy

class Win32Top(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.process_list = {}
        self.session_user = 0
        self.first_time = True
	computer_name = win32api.GetComputerName()
        #self.oWMI = win32com.client.GetObject(r"winmgmts:\\%s\root\cimv2" % computer_name)
        self.oWMI = win32com.client.GetObject(r"winmgmts:")
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

    def start(self):
        print "Start Win32 Top"
        gobject.timeout_add(1000, self.__update_info)
        gobject.timeout_add(3000, self.__update_session_info)

    def stop(self):
        print "Stop Win32 Top"

    def get_current_user_session(self):
        return self.session_user

    def proclist(self, uid):
        proclist = []
        for pid in self.process_list :
            if self.process_list[pid][0] == uid :
                proclist.append(pid)

        return proclist

    def proc_args(self, pid):
        try:
            return self.process_list(pid)[1]
        except:
            return ''
            
    def __update_session_info(self):
        qry = "Select * from Win32_ComputerSystem"
        qry = self.oWMI.ExecQuery(qry)
        if qry.count > 0:
            for result in qry:
                try:
                    username = str(result.UserName).split("\\")[-1]
                    users_list = self.quarterback.usersmanager.get_users()
                    for uid, uname, ufname in users_list:
                        if uname == username :
                            #print "[W32TOP] Session User : %s" % uid
                            self.session_user = uid
                            return True
                    self.session_user = 0
                    return True
                except:
                    self.session_user = 0
                    return True
        
        self.session_user = 0
        return True

    def __update_info(self):
        if self.first_time == True:
            print "[W32TOP] Initial process check start"

        qry = "SELECT * FROM Win32_Process"
        qry = self.oWMI.ExecQuery(qry)
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
                        uid_name = result.execMethod_('GetOwner').User
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
                            uid_name = result.execMethod_('GetOwner').User
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

                    
                
            
        
        
