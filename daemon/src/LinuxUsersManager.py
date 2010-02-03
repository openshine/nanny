#!/usr/bin/env python

# Copyright (C) 2009 Junta de Andalucia
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
import pwd

class LinuxUsersManager:
    def __init__(self):
        self.last_mdate = None
        self.users = None
        
    def get_users (self):
        if self.last_mdate == os.path.getmtime("/etc/passwd") and self.users != None:
            return self.users
            
        users=[]
        for user in pwd.getpwall() :
            if user.pw_dir.startswith("/home/") and os.path.isdir(user.pw_dir) :
                if len(user.pw_gecos.split(",")[0]) > 0 :
                    users.append((str(user.pw_uid), user.pw_name, user.pw_gecos.split(",")[0]))
                else:
                    users.append((str(user.pw_uid), user.pw_name, user.pw_name))

        self.last_mdate = os.path.getmtime("/etc/passwd")
        self.users = users
        return users

    def has_changes (self):
        if self.last_mdate == None :
            return True

        if self.last_mdate != os.path.getmtime("/etc/passwd"):
            return True

        return False
