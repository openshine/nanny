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

import gobject
import os

from twisted.internet import reactor
from time import localtime, strftime

(
SESSION_APPID,
WEB_APPID,
MAIL_APPID,
IM_APPID) = range(4)

iptables_weekdays = {"mon" : "Mon",
                     "tue" : "Tue",
                     "wed" : "Wed",
                     "thu" : "Thu",
                     "fri" : "Fri",
                     "sat" : "Sat",
                     "sun" : "Sun"}

services_ports = {WEB_APPID : "80, 443, 8080",
                  MAIL_APPID : "25, 110, 109, 995, 143, 220, 993, 465",
                  IM_APPID : "1863, 5222, 5269",
                  }

class Win32Firewall(gobject.GObject) :
    def __init__(self) :
        gobject.GObject.__init__(self)
        self.fw_status = [None, None, None, None]
        self.platform = None
        if self.__find_in_path("ipseccmd.exe") != None :
            self.platform = "xp"
            self.fw = "ipseccmd.exe"
        elif self.__find_in_path("ipsecpol.exe") != None :
            self.platform = "2000"
            self.fw = "ipsecpol.exe"
        else:
            pass

    def get_platform(self):
        return self.platform

    def set_appid_fwstatus(self, appid, block):
        if self.fw_status[appid] != None and self.fw_status[appid] == block :
            return

        if self.platform == "xp" or self.platform == "2000":
            port_params = ''
            for port in services_ports[appid].replace(" ","").split(",") :
                port_params = port_params + '-f 0=*:%s:TCP ' % port

            block_param = "-n BLOCK "
            if block == False:
                block_param = "-n PASS"
            
            os.system('%s -x -w REG -p "nanny_firewall" -r "nanny_appid_%s" %s %s > NUL' % (self.fw, appid, port_params, block_param))
            if self.fw_status[appid] != block :
                appid_name = { 1: "WEB", 2: "MAIL", 3: "IM"}
                print "[W32Filtering] %s ports block == %s" % (appid_name[appid], block)
                self.fw_status[appid] = block

    def start(self):
        if self.platform == "xp" or self.platform == "2000":
            os.system('%s -w reg -p "nanny_firewall" -y > NUL' % self.fw)
            os.system('%s -w reg -p "nanny_firewall" -o > NUL' % self.fw)
            self.set_appid_fwstatus(WEB_APPID, False)
            self.set_appid_fwstatus(MAIL_APPID, False)
            self.set_appid_fwstatus(IM_APPID, False)
        else:
            pass

    def stop(self):
        if self.platform == "xp" or self.platform == "2000":
            os.system('%s -w reg -p "nanny_firewall" -y > NUL' % self.fw)
            os.system('%s -w reg -p "nanny_firewall" -o > NUL' % self.fw)
        else:
            pass

    def __find_in_path(self, program):
        for dir in os.environ["PATH"].split(";") :
            if os.path.exists(os.path.join(dir, program)) :
                return os.path.join(dir, program)
        return None
        

class Win32Filtering(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

    def start(self):
        print "Start Win32 Filtering"
        self.win32fw = Win32Firewall()
        if self.win32fw.get_platform() != None:
            print "[W32Filtering] found Windows %s fw_tool" % self.win32fw.get_platform()
            self.win32fw.start()
            gobject.timeout_add(1000, self.__update_rules)

    def stop(self):
        print "Stop Win32 Filtering"
        if self.win32fw.get_platform() != None:
            self.win32fw.stop()

    def __update_rules(self):
        if self.win32fw.get_platform() == None:
            return True
        
        if self.quarterback.win32top.get_current_user_session() == 0 :
            self.win32fw.set_appid_fwstatus(WEB_APPID, False)
            self.win32fw.set_appid_fwstatus(MAIL_APPID, False)
            self.win32fw.set_appid_fwstatus(IM_APPID, False)
            return True

        session_uid = str(self.quarterback.win32top.get_current_user_session())
        blocks = self.quarterback.blocks

        for user_id in blocks.keys() :
            if int(user_id) == int(session_uid):
                for app_id in blocks[user_id].keys() :
                    if app_id == SESSION_APPID :
                        continue

                    if self.quarterback.get_available_time(user_id, app_id) == 0 :
                        self.win32fw.set_appid_fwstatus(int(app_id), True)
                        continue
                    try:
                        block_status, next_block = self.quarterback.is_blocked(user_id, app_id)
                    except:
                        print "[W32Filtering] Fail getting self.quarterback.is_blocked"
                        block_status = False

                    if block_status == True :
                        self.win32fw.set_appid_fwstatus(int(app_id), True)
                    else:
                        self.win32fw.set_appid_fwstatus(int(app_id), False)

        return True
        
gobject.type_register(Win32Filtering)
gobject.type_register(Win32Firewall)
