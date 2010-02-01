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
import gio
import os
import shutil
import pickle
import tempfile
from glob import glob

from twisted.internet import reactor, threads
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
        self.db_pools = {}
        self.pkg_filters_conf = {}

        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

    def start(self):
        print "Start Filter Manager"
        os.system("mkdir -p /var/lib/nanny/pkg_filters")
        self.custom_filters_db = self.__get_custom_filters_db()
        self.__start_packaged_filters()

    def stop(self):
        print "Stop Filter Manager"

    def check_domain(self, user_id, domain):
        pass

    def check_url(self, user_id, url):
        pass


    #Custom Filters methods
    #------------------------------------

    def __get_custom_filters_db(self):
        path = "/var/lib/nanny/customfilters.db"
        if os.path.exists(path) :
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
        sql_query = 'insert into customfilters ("uid", "is_black", "name", "description", "regexp") values ("%s", %s, "%s", "%s", "%s")' % (str(uid),
                                                                                                                                            int(is_black),
                                                                                                                                            name,
                                                                                                                                            description,
                                                                                                                                            regex)
        print sql_query
        query = self.custom_filters_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Adding Custom Filters"
            return False
        
    def list_custom_filters(self, uid):
        query = self.custom_filters_db.runQuery("select * from customfilters where uid = '%s'" % str(uid))
        block_d = BlockingDeferred(query)
        ret = []
        
        try:
            qr = block_d.blockOn()
            
            for f in qr :
                ret.append([ int(f[0]), unicode(f[3]), unicode(f[4]), unicode(f[5]), bool(f[2]) ])

            return ret
        except:
            print "Something goes wrong Listing Custom Filters"
            return ret
        

    def remove_custom_filter(self, list_id):
        query = self.custom_filters_db.runQuery('delete from customfilters where id=%s' % int(list_id))
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Removing Custom Filters"
            return False

    def update_custom_filter(self, list_id, name, description, regex):
        sql_query = 'update customfilters set name="%s", description="%s", regexp="%s" where id=%s' % (name,
                                                                                                      description,
                                                                                                      regex,
                                                                                                      int(list_id))

        print sql_query
        query = self.custom_filters_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Updating Custom Filter"
            return False
    

    #Packaged filters
    #-----------------------------------

    def __start_packaged_filters(self):
        ddbb = glob('/var/lib/nanny/pkg_filters/*/filters.db') + glob('/usr/share/nanny/pkg_filters/*/filters.db')
        for db in ddbb :
            self.db_pools[db] = adbapi.ConnectionPool('sqlite3', db,
                                                      check_same_thread=False,
                                                      cp_openfun=on_db_connect)

        if not os.path.exists("/var/lib/nanny/pkg_filters/conf") :
            for db in ddbb :
                self.pkg_filters_conf[db] = {"categories" : [],
                                             "users_info" : {}
                                             }
        else:
            db = open("/var/lib/nanny/pkg_filters/conf", 'rb')
            self.pkg_filters_conf = pickle.load(db)
            db.close()
            for rdb in list(set(self.pkg_filters_conf.keys()) - set(ddbb)) :
                print "Remove conf of pkg_list (%s)" % rdb
                self.pkg_filters_conf.pop(rdb)
            for db in ddbb :
                if not self.pkg_filters_conf.has_key(db) :
                    print "Add missing conf of pkg_list (%s)" % db
                    self.pkg_filters_conf[db] = {"categories" : [],
                                                 "users_info" : {}
                                                 }
            self.__save_pkg_filters_conf()
            

    def __save_pkg_filters_conf(self):
        output = open("/var/lib/nanny/pkg_filters/conf", 'wb')
        pickle.dump(self.pkg_filters_conf, output)
        output.close()
    
    def __get_categories_from_db(self, db):
        if len(self.pkg_filters_conf[db]["categories"]) == 2 :
            if os.path.getmtime(db) == self.pkg_filters_conf[db]["categories"][0] :
                return self.pkg_filters_conf[db]["categories"][1]
            
        sql_query = 'SELECT category FROM black_domains UNION SELECT category FROM black_urls UNION SELECT category FROM white_domains UNION SELECT category FROM white_urls'
        query = self.db_pools[db].runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            cats = []
            for c in qr :
                if c[0] != "may_url_blocked" :
                    cats.append(c[0])
                
            tmp_cat = [os.path.getmtime(db), cats]
            self.pkg_filters_conf[db]["categories"] = tmp_cat
            self.__save_pkg_filters_conf()
            return self.pkg_filters_conf[db]["categories"][1]
        except:
            print "Something goes wrong getting categories from %s" % db
            return []
        
    def add_pkg_filter(self, name, description, path):
        temp_dir = tempfile.mkdtemp(prefix="filter_", dir="/var/lib/nanny/pkg_filters/")
        try:
            d = threads.deferToThread(self.__copy_pkg_filter, path, os.path.join(temp_dir, "filters.db"))
            block_d = BlockingDeferred(d)
            qr = block_d.blockOn()
            if qr == True :
                fd = open(os.path.join(temp_dir, "filters.metadata"), "w")
                fd.write("Name=%s\n" % name)
                fd.write("Comment=%s\n" % description)
                fd.close()
            else:
                shutil.rmtree(temp_dir)
                return False
                
            self.db_pools[os.path.join(temp_dir, "filters.db")] = adbapi.ConnectionPool('sqlite3',
                                                                                        os.path.join(temp_dir, "filters.db"),
                                                                                        check_same_thread=False,
                                                                                        cp_openfun=on_db_connect)
            self.pkg_filters_conf[os.path.join(temp_dir, "filters.db")] = {"categories" : [],
                                                                           "users_info" : {}
                                                                           }
            self.__save_pkg_filters_conf()
            return True
        except:
            print "Something goes wrong Adding PKG Filter"
            shutil.rmtree(temp_dir)
            return False
        
    def __copy_pkg_filter(self, orig, dest):
        try:
            print "Coping %s" % orig
            if os.path.exists(dest) :
                print "Making Backup file"
                gio.File(dest).move(gio.File(dest + ".bak"))
                
            gio.File(orig).copy(gio.File(dest))
            print "Copied %s in %s" % (orig, dest)
            
            if os.path.exists(dest + ".bak") :
                print "Removing Backup file"
                os.unlink(dest + ".bak")
            return True
        except:
            print "Copy failed! (%s, %s)" % (orig, dest)
            if os.path.exists(dest + ".bak") :
                print "Revert to backup file"
                gio.File(dest + ".bak").move(gio.File(dest))
            return False

    def remove_pkg_filter(self, pkg_id):
        for id, ro in self.list_pkg_filter() :
             if id == pkg_id and ro == False:
                 if self.db_pools.has_key(pkg_id) :
                     db = self.db_pools.pop(pkg_id)
                     db.close()
                     self.pkg_filters_conf.pop(pkg_id)
                     self.__save_pkg_filters_conf()
                     db_dir = os.path.dirname(pkg_id)
                     print "Removing dir %s" % db_dir
                     shutil.rmtree(db_dir)
                     return True
        

    def update_pkg_filter(self, pkg_id, new_db):
        for id, ro in self.list_pkg_filter() :
            if id == pkg_id and ro == False:
                d = threads.deferToThread(self.__copy_pkg_filter, new_db, pkg_id)
                block_d = BlockingDeferred(d)
                qr = block_d.blockOn()
                if qr == True :
                    return True
                else:
                    return False
        return False

    def list_pkg_filter(self):
        ret = []
        for x in self.pkg_filters_conf.keys():
            if x.startswith("/usr") :
                ro = True
            else:
                ro = False
            
            ret.append([unicode(x), ro])
                
        return ret

    def get_pkg_filter_metadata(self, pkg_id):
        path = os.path.dirname(pkg_id)
        if not os.path.exists(path) :
            return ['', '']
        
        name = ""
        description = ""
        
        if os.path.exists(os.path.join(path, "filters.metadata")) :
            fd = open(os.path.join(path, "filters.metadata"), "r")
            for line in fd.readlines():
                l = line.strip("\n")
                if l.startswith("Name=") :
                    name = l.replace("Name=", "")
                elif l.startswith("Comment=") :
                    description = l.replace("Comment=", "")
                else:
                    continue
            fd.close()

        return [name, description]

    def set_pkg_filter_metadata(self, pkg_id, name, description):
        for id, ro in self.list_pkg_filter() :
            if id == pkg_id and ro == False:
                path = os.path.dirname(pkg_id)
                if os.path.exists(path) :
                    fd = open(os.path.join(path, "filters.metadata"), "w")
                    fd.write("Name=%s\n" % name)
                    fd.write("Comment=%s\n" % description)
                    fd.close()
                    return True
        
        return False
            
    def get_pkg_filter_user_categories(self, pkg_id, uid):
        try:
            name = ""
            description = ""
            categories = self.__get_categories_from_db(pkg_id)
            if self.pkg_filters_conf[pkg_id]["users_info"].has_key(uid) :
                user_categories = self.pkg_filters_conf[pkg_id]["users_info"][uid]
            else:
                user_categories = []

            if not set(user_categories).issubset(set(categories)) :
                tmp_user_categories = []
                for ucat in user_categories :
                    if ucat in categories:
                        tmp_user_categories.append(ucat)
                user_categories = tmp_user_categories
                self.pkg_filters_conf[pkg_id]["users_info"][uid] = user_categories
                self.__save_pkg_filters_conf()
            
        except:
            return [[], []]
            
        return [categories, user_categories]

    def set_pkg_filter_user_categories(self, pkg_id, uid, user_categories):
        categories = self.__get_categories_from_db(pkg_id)
        tmp_user_categories = []
        
        if not set(user_categories).issubset(set(categories)) :
            for ucat in user_categories :
                if ucat in categories:
                    tmp_user_categories.append(ucat)
        else:
            user_categories = tmp_user_categories
        
        self.pkg_filters_conf[pkg_id]["users_info"][uid] = user_categories
        self.__save_pkg_filters_conf()
        return True

