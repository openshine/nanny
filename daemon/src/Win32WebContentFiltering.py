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
from twisted.application import internet, service
from twisted.web import server
from twisted.enterprise import adbapi

from nanny.daemon.proxy.TwistedProxy import ReverseProxyResource as ProxyService
from nanny.daemon.proxy.Controllers import WebDatabase

PORT_START_NUMBER=53000
WEBDATABASE='C:\\WINDOWS\\nanny_data\\webs.db'

def ipt(cmd) :
    return os.system("/sbin/iptables %s > /dev/null 2>&1" % cmd)

class Win32WebContentFiltering(gobject.GObject) :
    def __init__(self, quarterback, app) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.app = app

        database_exists = False
        if os.path.exists(WEBDATABASE) :
            database_exists = True
        
        self.dbpool = adbapi.ConnectionPool('sqlite3', WEBDATABASE, check_same_thread=False)
        self.webdb = WebDatabase(self.dbpool)

        if database_exists == False :
            self.webdb.create()
        
        self.services={}
        
        reactor.addSystemEventTrigger("after", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

        self.quarterback.connect("add-wcf-to-uid", self.__start_proxy)
        self.quarterback.connect("remove-wcf-to-uid", self.__stop_proxy)
        
    def start(self):
        print "Start Win32 Web Content Filtering"
        for uid in self.quarterback.wcf_uid_list :
            self.__start_proxy(self.quarterback, uid)

    def stop(self):
        print "Stop Win32 Web Content Filtering"
        for uid in self.services.keys() :
            self.__stop_proxy(self.quarterback, uid)

    def __start_proxy(self, quarterback, uid):
        pass
#         if not self.services.has_key(uid) :
#             root = ProxyService(uid, quarterback.filter_manager)
#             sc = service.IServiceCollection(self.app)
#             site = server.Site(root)
            
#             for port in range(PORT_START_NUMBER, PORT_START_NUMBER+5000) :
#                 try:
#                     i = internet.TCPServer(port, site)
#                     i.setServiceParent(sc)
#                 except:
#                     continue
                
#                 self.services[uid]=(i, port)
#                 self.__add_rule(uid, port)
#                 return
        
    def __stop_proxy(self, quarterback, uid):
        pass
#         if not self.services.has_key(uid) :
#             return True
#         else:
#             i,port = self.services.pop(uid)
#             i.stopService()
#             self.__remove_rule(uid, port)

    def __add_rule(self, uid, port):
        ret = ipt("-t nat -A OUTPUT -p tcp -m owner --uid-owner %s -m tcp --dport 80 --syn -j REDIRECT --to-ports %s" % (uid, port))
        if ret == 0:
            print "Redirecting of user (%s) from 80 to %s" % (uid, port)

    def __remove_rule(self, uid, port):
        ret = ipt("-t nat -D OUTPUT -p tcp -m owner --uid-owner %s -m tcp --dport 80 --syn -j REDIRECT --to-ports %s" % (uid, port))
        if ret == 0:
            print "Remove Redirecting of user (%s) from 80 to %s" % (uid, port)

    


    
