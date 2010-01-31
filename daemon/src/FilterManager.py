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

import gobject
import os
from twisted.internet import reactor
from twisted.enterprise import adbapi

import nanny.gregex
from BlockingDeferred import BlockingDeferred

def regexp(expr, item):
    return bool(nanny.gregex.regexp(expr, item))

def on_db_connect(conn):
    conn.create_function("regexp", 2, regexp)

class FilterManager (gobject.GObject) :
    def __init__(self, quarterback):
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.custom_filters_db = None

        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

    def start(self):
        os.system("mkdir -p /var/lib/nanny/lists")
        self.custom_filters_db = self.__get_custom_filters_db()

    def stop(self):
        pass

    def check_domain(self, user_id, domain):
        pass

    def check_url(self, user_id, url):
        pass

    def __open_db_pool(self, path):
        return adbapi.ConnectionPool('sqlite3', path,
                                     check_same_thread=False,
                                     cp_openfun=on_db_connect)

    #Custom Filters methods
    #------------------------------------

    def __get_custom_filters_db(self):
        if os.path.exists("/var/lib/nanny/customfilters.db") :
            return adbapi.ConnectionPool('sqlite3', path,
                                         check_same_thread=False,
                                         cp_openfun=on_db_connect)
        else:
            db = adbapi.ConnectionPool('sqlite3', path,
                                       check_same_thread=False,
                                       cp_openfun=on_db_connect)
            db.runOperation('create table customfilters (id INTEGER PRIMARY KEY, uid text, is_black bool, name text, description text, regexp text)')
            print "Created custom filters db"
            return db

    def add_custom_filter(self, uid, is_black, name, description, regex):
        self.custom_filters_db.runOperation('insert into customfilters values ("%s", %s, "%s", "%s", "%s")' % (str(uid),
                                                                                                               bool(is_black),
                                                                                                               name,
                                                                                                               description,
                                                                                                               regex))                                  
        
    def list_custom_filter(self, uid):
        query = self.custom_filters_db.runQuery("select * from customfilters where uid = '%s'" % str(uid))
        block_d = BlockingDeferred(query)
        ret = []
        
        try:
            qr = block_d.blockOn()
            
            for f in qr :
                ret.append([ int(f[0]), str(f[3]), str(f[4]), bool(f[2]) ])

            return ret
        except:
            print "Something goes wrong Listing Custom Filters"
            return ret
        

    def remove_custom_filter(self, list_id):
        self.custom_filters_db.runOperation('delete from customfilters where id=%s' % int(list_id))    
    
        

    
