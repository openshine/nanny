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

class Win32Filtering(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)
        
        self.quarterback.connect("update-blocks", self.__update_blocks_cb)

    def start(self):
        print "Start Win32 Filtering"
        self.__update_blocks_cb(self.quarterback, self.quarterback.blocks)

    def stop(self):
        print "Stop Win32 Filtering"

    def __update_blocks_cb(self, quarterback, blocks):
        #Create pre-chain
        rules=[]
        for user_id in blocks.keys() :
            for app_id in blocks[user_id].keys() :
                if app_id == SESSION_APPID :
                    continue

                if quarterback.get_available_time(user_id, app_id) == 0 :
                    rules.append(
                            (user_id,
                             strftime("%a", localtime()),
                             "00:01",
                             "23:59",
                             services_ports[app_id]
                             )
                        )
                
                to_block = quarterback.get_blocks(user_id, app_id)
                for week_day in to_block.keys() :
                    for i_time, e_time in to_block[week_day] :
                        rules.append(
                            (user_id,
                             iptables_weekdays[week_day],
                             i_time,
                             e_time,
                             services_ports[app_id]
                             )
                            )
            
        #apply rules firewall
        print ("update_firewall_rules : WIP")
        
gobject.type_register(Win32Filtering)
