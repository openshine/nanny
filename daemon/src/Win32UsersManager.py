#!/usr/bin/env python

# Copyright (C) 2009,2010 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
#   Cesar Garcia Tapia <cesar.garcia.tapia at openshine.com>
#   Luis de Bethencourt <luibg at openshine.com>
#   Pablo Vieytes <pvieytes at openshine.com>
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

class Win32UsersManager:
    def __init__(self):
        self.last_time = None
        self.users = None
        
    def get_users (self):
        if self.last_time != None and time.time() - self.last_time <= 60 :
            return self.users

        users=[]
        #oWMI = win32com.client.GetObject(r"winmgmts:\\.\root\cimv2")
        oWMI = win32com.client.GetObject(r"winmgmts:")
        qry = "Select * from Win32_UserAccount Where LocalAccount = True and Disabled = False"
        qry = oWMI.ExecQuery(qry)
        if qry.count > 0:
            for result in qry:
                uid = str(result.SID).split("-")[-1]
                if int(uid) >= 1000 and result.Name != "HomeGroupUser$" :
                    users.append((uid, unicode(result.Name), unicode(result.FullName)))
        self.last_time = time.time()
        self.users = users
        return users

    def has_changes (self):
        if self.last_time == None :
            return True
        
        if time.time() - self.last_time > 60 :
            return True
        
        return False
