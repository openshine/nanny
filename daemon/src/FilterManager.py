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
import gio
import os
import hashlib
import sys
import json
import etld

import errno

import shutil
import pickle
import tempfile
import tarfile
from glob import glob

from twisted.internet import reactor, threads, defer
from twisted.enterprise import adbapi

from BlockingDeferred import BlockingDeferred

from ctypes import *
if os.name == "posix" :
    g = cdll.LoadLibrary("libglib-2.0.so")
elif os.name == "nt":
    g = cdll.LoadLibrary("libglib-2.0-0.dll")

g.g_regex_match_simple.restype=c_int
g.g_regex_match_simple.argtypes=[c_wchar_p, c_wchar_p, c_int, c_int]

import re

def regexp(expr, item):
    try:
        #ret = g.g_regex_match_simple(expr, item, 0, 0)
        p = re.compile(expr)
        ret = bool(p.match(item))
	#print "GREGEXP>> expr: '%s' item: '%s' ----> %s" % (expr, item, ret) 
	return ret
    except:
        print "Regex failure"
        return False

def on_db_connect(conn):
    conn.create_function("gregexp", 2, regexp)

if os.name == "posix" :
    NANNY_DAEMON_DATA = "/var/lib/nanny/"
elif os.name == "nt" :
    if not hasattr(sys, "frozen") :
        file_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for x in range(6):
            file_dir = os.path.dirname(file_dir)
        root_path = file_dir
        
        NANNY_DAEMON_DATA = os.path.join(root_path, "var", "lib", "nanny")
    else:        
        NANNY_DAEMON_DATA = os.path.join(os.environ["ALLUSERSPROFILE"], "Gnome", "nanny")

#Nanny daemon blacklists dir is to storage the admin blacklists and sys blacklists if for
#read-only blacklists, for example blacklists provided by packages
NANNY_DAEMON_BLACKLISTS_DIR = os.path.join(NANNY_DAEMON_DATA, "blacklists")
NANNY_DAEMON_BLACKLISTS_SYS_DIR = os.path.join(NANNY_DAEMON_DATA, "sysblacklists") 
NANNY_DAEMON_BLACKLISTS_CONF_FILE = os.path.join(NANNY_DAEMON_DATA, "bl_conf.db")

PKG_STATUS_ERROR_NOT_EXISTS = -2
PKG_STATUS_ERROR_INSTALLING_NEW_BL = -1
PKG_STATUS_ERROR = 0
PKG_STATUS_INSTALLING = 1
PKG_STATUS_UPDATING = 2
PKG_STATUS_READY = 3
PKG_STATUS_READY_UPDATE_AVAILABLE = 4

def mkdir_path(path):
    try:
        os.makedirs(path)
    except os.error, e:
        if e.errno != errno.EEXIST:
            raise

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
        mkdir_path(os.path.join(NANNY_DAEMON_DATA, "pkg_filters"))
        mkdir_path(NANNY_DAEMON_BLACKLISTS_DIR)
        
        self.custom_filters_db = self.__get_custom_filters_db()
        self.__start_packaged_filters()

    def stop(self):
        print "Stop Filter Manager"


    #Custom Filters methods
    #------------------------------------

    def __get_custom_filters_db(self):
        path = os.path.join(NANNY_DAEMON_DATA, "customfilters.db")
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
        if os.path.exists(NANNY_DAEMON_BLACKLISTS_CONF_FILE):
            with open(NANNY_DAEMON_BLACKLISTS_CONF_FILE, 'rb') as f:
                self.pkg_filters_conf = pickle.load(f)
        
        for pkg_id in self.pkg_filters_conf.keys():
            self._save_pkg_filters_conf()
            if self.pkg_filters_conf[pkg_id]["status"] == PKG_STATUS_READY \
            or self.pkg_filters_conf[pkg_id]["status"] == PKG_STATUS_READY_UPDATE_AVAILABLE:
                db = os.path.join(NANNY_DAEMON_BLACKLISTS_DIR,
                                  "%s.db" % (pkg_id))
                self.db_pools[pkg_id] = adbapi.ConnectionPool('sqlite3', db,
                                                              check_same_thread=False,
                                                              cp_openfun=on_db_connect)
                print "Added to db pool -> %s" % pkg_id

    def _save_pkg_filters_conf(self):
        output = open(NANNY_DAEMON_BLACKLISTS_CONF_FILE, 'wb')
        pickle.dump(self.pkg_filters_conf, output)
        output.close()
        
    def __get_categories_from_db(self, pkg_id):
        try:
            return self.pkg_filters_conf[pkg_id]["pkg_info"]["categories"]
        except:
            return []
  
    def add_pkg_filter(self, url):
        pkg_id = hashlib.md5().hexdigest()
        if pkg_id in self.pkg_filters_conf.keys() :
            return False
        
        self.pkg_filters_conf[pkg_id] = {"users_info" : {},
                                         "pkg_info": {},
                                         "status" : PKG_STATUS_INSTALLING,
                                         "update_url" : url
                                         }
        
        reactor.callInThread(self.__download_new_pkg, pkg_id, url, self)
        return True
        
    def __download_new_pkg(self, pkg_id, url, fm):
        import sqlite3
        import urllib2
        import urlparse 
        import bz2
        
        try:
            pkg_info = json.load(urllib2.urlopen(url))
            fm.pkg_filters_conf[pkg_id]["pkg_info"] = pkg_info

            base_filename = pkg_info["base"]
            base_url = urlparse.urljoin(url, base_filename)
            dest_file = os.path.join(NANNY_DAEMON_BLACKLISTS_DIR,
                                     "%s-%s" % (pkg_id, base_filename))
            dest_db = os.path.join(NANNY_DAEMON_BLACKLISTS_DIR,
                                   "%s.db" % (pkg_id))

            if os.path.exists(dest_file):
                os.unlink(dest_file)
            
            if os.path.exists(dest_db):
                os.unlink(dest_db)

            df = open(dest_file, "wb")
            df.write(urllib2.urlopen(base_url).read())
            df.close()

            df_uc = bz2.BZ2File(dest_file, "r")
            db_conn = sqlite3.connect(dest_db)

            sql=''

            for line in df_uc.readlines():
                sql = sql + line
                if sqlite3.complete_statement(sql) :    
                    c = db_conn.cursor()
                    try:
                        c.execute(sql)
                    except:
                        pass
                    sql = ''

            db_conn.commit()
            db_conn.close()
            df_uc.close()

            os.unlink(dest_file)

            fm.pkg_filters_conf[pkg_id]["status"]=PKG_STATUS_READY
            fm.db_pools[pkg_id] = adbapi.ConnectionPool('sqlite3', dest_db,
                                                        check_same_thread=False,
                                                        cp_openfun=on_db_connect)
            print "Added to db pool -> %s" % pkg_id  
            threads.blockingCallFromThread(reactor, 
                                           fm._save_pkg_filters_conf)
        except:
            if os.path.exists(dest_file):
                os.unlink(dest_file)
            
            if os.path.exists(dest_db):
                os.unlink(dest_db)
            
            fm.pkg_filters_conf[pkg_id]["pkg_info"]={}
            fm.pkg_filters_conf[pkg_id]["status"]=PKG_STATUS_ERROR_INSTALLING_NEW_BL
            threads.blockingCallFromThread(reactor, 
                                           fm._save_pkg_filters_conf)
    
    def remove_pkg_filter(self, pkg_id):
        dest_db = os.path.join(NANNY_DAEMON_BLACKLISTS_DIR,
                               "%s.db" % (pkg_id))
        if os.path.exists(dest_db):
            if pkg_id in self.db_pools.keys():
                db = self.db_pools.pop(pkg_id)
                db.close()
            os.unlink(dest_db)
        try:
            self.pkg_filters_conf.pop(pkg_id)
            self._save_pkg_filters_conf()
            print "Removed from db pool -> %s" % pkg_id
        except:
            pass
        
        return True
                
    def update_pkg_filter(self, pkg_id, new_db):
        pass

    def list_pkg_filter(self):
        ret = []
        for x in self.pkg_filters_conf.keys():
            ret.append([x, False])
                
        return ret
    
    def get_pkg_filter_metadata(self, pkg_id):
        try:
            if self.pkg_filters_conf[pkg_id]["pkg_info"].has_key("metadata"):
                ret = [self.pkg_filters_conf[pkg_id]["pkg_info"]["metadata"]["name"],
                       self.pkg_filters_conf[pkg_id]["pkg_info"]["metadata"]["provider"]]
                return ret
        except:
            pass

        return [pkg_id, 'Unknown information']
    
    def set_pkg_filter_metadata(self, pkg_id, name, description):
        #Deprecated !!
        return True
    
    def get_pkg_filter_user_categories(self, pkg_id, uid):
        try:
            return_categories = []

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
                self._save_pkg_filters_conf()

            for category in categories:
                if category in user_categories:
                    return_categories.append ((category, True))
                else:
                    return_categories.append ((category, False))

            return return_categories
            
        except:
            return []

    def set_pkg_filter_user_categories(self, pkg_id, uid, user_categories):
        categories = self.__get_categories_from_db(pkg_id)
        tmp_user_categories = []
        
        if not set(user_categories).issubset(set(categories)) :
            for ucat in user_categories :
                if ucat in categories:
                    tmp_user_categories.append(ucat)
            user_categories = tmp_user_categories
        
        self.pkg_filters_conf[pkg_id]["users_info"][uid] = user_categories
        self._save_pkg_filters_conf()
        return True

    #Check methods
    #------------------------------------

    def check_domain_defer (self, uid, domain):
        d = defer.Deferred()
        reactor.callLater(0.05, d.callback, self.check_domain(uid, domain))
        return d

    def check_url_defer(self, uid, host, port, request, rest, pre_check):     
        d = defer.Deferred()
        reactor.callLater(0.05, d.callback, self.check_url(uid, host, port, request, rest, pre_check))
        return d
        
    def check_domain(self, uid, domain):
        print "Check Domain"
        
        idomain = ''
        domain_list = domain.split(".")
        domain_list.reverse()
        for x in domain_list:
            idomain = idomain + x + "."
        idomain = idomain[:-1]

        print "Idomain : %s" % idomain

        blacklisted_categories = []
        custom_black=False
        
        #Search in customfilters
        sql_query = 'select distinct is_black from customfilters where uid="%s" and gregexp( "(.+\.|)" || regexp || ".*" , "%s")' % (uid, domain)
        query = self.custom_filters_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            if len(qr) > 0 :
                for x in qr :
                    if x[0] == 0:
                        print "Custom WhiteListed"
                        return [False, False, []]
                    if x[0] == 1:
                        custom_black = True
                
        except:
            print "Something goes wrong checking Custom Filters"
            return [[False, False], []]
        

        #Search in whitelists
        for db in self.pkg_filters_conf.keys():
            if self.pkg_filters_conf[db]["users_info"].has_key(uid) :
                if len(self.pkg_filters_conf[db]["users_info"][uid]) > 0 :
                    sql_query = 'select distinct category from white_domains where gregexp(regexp || "(|\..+)" , "%s")' % idomain
                    query = self.db_pools[db].runQuery(sql_query)
                    block_d = BlockingDeferred(query)
                    
                    try:
                        qr = block_d.blockOn()
                        if len(qr) > 0:
                            return [[False, False], []]
                        
                    except:
                        print "Something goes wrong checking domains"
                        return [[False, False], []]

        if custom_black == True :
            print "Custom BlackListed"
            return [[True, False], []]

        #Search in blacklists
        for db in self.pkg_filters_conf.keys():
            if self.pkg_filters_conf[db]["users_info"].has_key(uid) :
                if len(self.pkg_filters_conf[db]["users_info"][uid]) > 0 :
                    
                    category_c = ''
                    for cat in self.pkg_filters_conf[db]["users_info"][uid] :
                        if category_c != '' :
                            category_c = category_c + " OR " + "category='%s' " % cat
                        else:
                            category_c = "category='%s' " % cat
                    category_c = category_c + "OR category='may_url_blocked'"
                            
                    regexp_c = 'gregexp(regexp || "(|\..+)" , "%s")' % idomain
                    sql_query = 'select distinct category from black_domains where (%s) AND (%s)' % (category_c, regexp_c)
                    query = self.db_pools[db].runQuery(sql_query)
                    block_d = BlockingDeferred(query)
                    
                    try:
                        qr = block_d.blockOn()
                        print qr
                        for cat in qr :
                            blacklisted_categories.append(cat[0])
                    except:
                        print "Something goes wrong checking domains"
                        return [[False, False], []]

        if len (blacklisted_categories) > 0 :
            if "may_url_blocked" in blacklisted_categories :
                blacklisted_categories.pop(blacklisted_categories.index("may_url_blocked"))
                if len (blacklisted_categories) > 0 :
                    return [[True, True], blacklisted_categories]
                else:
                    return [[False, True], blacklisted_categories]
            else:
                return [[True, False], blacklisted_categories]

        return [[False, False], []]
                

    def check_url(self, uid, host, port, request, rest, pre_check):
        if pre_check[0] == True :
            print 'Uri Validation stopped because domain is blocked, %s' % (host + request.uri)
            return False, request, rest, host, port

        if pre_check[1] == False :
            print 'Uri validation verified in pre-check %s' % (host + request.uri)
            return True, request, rest, host, port

        uri = host + request.uri
        is_ok = True
        blacklisted_categories = []

        #Search in whitelists
        for db in self.pkg_filters_conf.keys():
            if self.pkg_filters_conf[db]["users_info"].has_key(uid) :
                if len(self.pkg_filters_conf[db]["users_info"][uid]) > 0 :
                    sql_query = 'select distinct category from white_urls where gregexp(regexp || ".*" , "%s")' % uri
                    query = self.db_pools[db].runQuery(sql_query)
                    block_d = BlockingDeferred(query)
                    
                    try:
                        qr = block_d.blockOn()
                        if len(qr) > 0:
                            print 'Uri validation verified whitelisted %s' % (host + request.uri)
                            return True, request, rest, host, port
                        
                    except:
                        print "Something goes wrong checking whitelisted urls"
                        return True, request, rest, host, port
        
        #Search in blacklists
        for db in self.pkg_filters_conf.keys():
            if self.pkg_filters_conf[db]["users_info"].has_key(uid) :
                if len(self.pkg_filters_conf[db]["users_info"][uid]) > 0 :
                    sql_query = 'select distinct category from black_urls where gregexp(regexp || ".*" , "%s")' % uri
                    query = self.db_pools[db].runQuery(sql_query)
                    block_d = BlockingDeferred(query)
                    
                    try:
                        qr = block_d.blockOn()
                        if len(qr) > 0:
                            for cat in qr :
                                blacklisted_categories.append(cat[0])
                    except:
                        print "Something goes wrong checking blacklisted urls"
                        return True, request, rest, host, port

        if len (blacklisted_categories) > 0 :
            print 'Uri validation stopped because is blacklisted %s [%s]' % (host + request.uri, blacklisted_categories)
            return False, request, rest, host, port
        
        print 'Uri validation passed by default  %s' % (host + request.uri)
        return True, request, rest, host, port

    def __split_url(self, url):
        """Split a url in several pieces, returning a tuple with each of that pieces.
        It will also remove the user (http://user:password@domain.com) and the port (http://domain.com:8080) 

        Example: With the url "http://www.google.com/test/extra/index.html", the function will return this pieces:

        protocol: The protocol used by the url (in the example, "http").
        domain: The domain of the url (in the example, "google.com").
        subdomain: The subdomain of the url (in the example, "www").
        firstlevel: The first level of the path (in the example, "test").
        extra: The part of the URL not contained in the previous pieces (in the example, "extra/index.html").   
        """

        url = url.lower ()

        splitted_url = url.split ("://")
        if len (splitted_url) > 1:
            protocol = splitted_url[0]
            url = splitted_url[1]
        else:
            protocol = 'http'

        if protocol != "http" and protocol != "https":
            return (None, None, None, None, None) 

        parsed_url = urlparse ("%s://%s" % (protocol, url)) 

        domain_string = parsed_url.netloc
        path_string = parsed_url.path

        if not domain_string:
            return (None, None, None, None, None)
        else:
            if domain_string.find ("@") > -1:
                domain_string = domain_string.split ("@")[1]
            if domain_string.find (":") > -1:
                domain_string = domain_string.split (":")[0]

        etld_object = etld.etld()
        try:
            subdomain, domain = etld_object.parse ("%s://%s" % (protocol, domain_string))
        except:
            return (None, None, None, None, None)

        if subdomain == "":
            subdomain = None

        if path_string:
            path_pieces = path_string.split ("/")

            firstlevel = path_pieces[1] if len (path_pieces) > 1 and path_pieces[1] else None
            extra = "/".join (path_pieces [2:]) if len (path_pieces) > 2 and path_pieces[2] else None
        else:
            firstlevel = None
            extra = None

        return (protocol, domain, subdomain, firstlevel, extra)
