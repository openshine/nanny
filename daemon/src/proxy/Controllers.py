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

from twisted.enterprise import adbapi
from twisted.internet import reactor, defer
from twisted.internet.defer import AlreadyCalledError
from twisted.python import failure
from twisted.web import client

import os
import time
import tempfile
import tarfile

import urlparse
from urllib import quote as urlquote

TIMEOUT = 0.05                  # Set the timeout for poll/select

class BlockingDeferred(object):
    """Wrap a Deferred into a blocking API."""
    
    def __init__(self, d):
        """Wrap a Deferred d."""
        self.d = d
        self.finished = False
        self.count = 0

    def blockOn(self):
        """Call this to block and get the result of the wrapped Deferred.
        
        On success this will return the result.
        
        On failure, it will raise an exception.
        """
        
        self.d.addBoth(self.gotResult)
        self.d.addErrback(self.gotFailure)
        
        while not self.finished:
            reactor.iterate(TIMEOUT)
            self.count += 1
        
        if isinstance(self.d.result, dict):
            f = self.d.result.get('failure', None)
            if isinstance(f, failure.Failure):
                f.raiseException()
        return self.d.result

    def gotResult(self, result):
        self.finished = True
        return result
        
    def gotFailure(self, f):
        self.finished = True
        # Now make it look like a success so the failure isn't unhandled
        return {'failure':f}

class DansGuardianImporter(object):
    def __init__(self, dbpool, list_url, uid, name, description):
        tmpfd, self.tmp_filename = tempfile.mkstemp()
        os.close(tmpfd)
        
        self.d = client.downloadPage(list_url, self.tmp_filename)
        self.finished = False
        self.count = 0
        
        self.dbpool = dbpool
        self.list_url = list_url
        self.uid = uid
        self.name = name
        self.description = description

    def blockOn(self):
        try:
            self.d.addCallback(self.__dans_guardian_list_downloaded_cb, self.tmp_filename,
                           self.uid, self.name, self.description, self.list_url)
            self.d.addErrback(self.gotFailure)

            while not self.finished:
                reactor.iterate(TIMEOUT)
                self.count += 1

            if isinstance(self.d.result, dict):
                f = self.d.result.get('failure', None)
                if isinstance(f, failure.Failure):
                    f.raiseException()

            return self.d.result
        except AlreadyCalledError:
            return False

    def __dans_guardian_list_downloaded_cb(self, result, list_file, uid, name, description, list_url):
        try:
            print "Importing '%s' List" % name
            tfile = tarfile.open(list_file)

            query = self.dbpool.runInteraction(self.__create_dg_orig_register, uid, name, description, list_url)
            block_d = BlockingDeferred(query)

            origin_id = None
            try:
                origin_id = block_d.blockOn()
            except:
                print "Something wrong creating dg origin register"
                self.finished = True
                return False

            for member in tfile :
                m_fd = None
                regex_type = None
                if "whitelist" in member.name.lower() :
                    is_black = False
                else:
                    is_black = True

                if os.path.basename(member.name) == "urls" and member.isfile():
                    m_fd = tfile.extractfile(member.name)
                    regex_type = "url"
                    category = os.path.basename(os.path.dirname(member.name))
                elif os.path.basename(member.name) == "domains" and member.isfile():
                    m_fd = tfile.extractfile(member.name)
                    regex_type = "domain"
                    category = os.path.basename(os.path.dirname(member.name))
                else:
                    continue

                regex_list = []
                i = 0
                for line in m_fd.readlines() :
                    regex = line.replace("\r","").replace("\n", "").replace(" ","")
                    if len(regex) > 0 :
                        regex_list.append((regex.decode("iso8859-15".lower()),))

                    if len(regex_list) >= 10000 :
                        query = self.dbpool.runInteraction(self.__register_dg_website , is_black, uid, origin_id, category, regex_type, regex_list)
                        block_d = BlockingDeferred(query)
                        reg_web_id = None
                        try:
                            reg_web_id = block_d.blockOn()
                        except:
                            print "Something wrong registering web regex : (%s, %s, %s)" % (len(regex_list), category, i)
                        regex_list = []
                        i = i + 1
                    
                
                query = self.dbpool.runInteraction(self.__register_dg_website , is_black, uid, origin_id, category, regex_type, regex_list)
                block_d = BlockingDeferred(query)
                reg_web_id = None
                try:
                    reg_web_id = block_d.blockOn()
                except:
                    print "Something wrong registering web regex : (%s, %s, %s)" % (len(regex_list), category, i)
                

            print "Imported '%s' List" % name
            self.finished = True
            return True
        except:
            print "Probably is not a DansGuardianList"
            self.finished = True
            return False
            
    def __create_dg_orig_register(self, txn, uid, name, description, list_url):
        timestamp = int(time.time())
        sql="INSERT INTO Origin ('name', 'uid', 'timestamp', 'description', 'is_black') VALUES ('%s', '%s', %s, '%s', 1)" % (name, uid, timestamp, description)
        txn.execute(sql)

        txn.execute("SELECT last_insert_rowid()")
        ret = txn.fetchall()

        origin_id = ret[0][0]
        return origin_id

    def __register_dg_website(self, txn, is_black, uid, origin_id, category, regex_type, regex_list):
        if len(regex_list) == 0 :
            return

        #print "Registering %s websites (%s)" % (category, len(regex_list))
        sql="INSERT INTO Website ('is_black', 'uid', 'origin_id', 'category', 'type', 'body') VALUES (%s, '%s', %s, '%s', '%s', ?)" % (int(is_black), uid, int(origin_id), category, regex_type)
        txn.executemany(sql, regex_list)
        

    def gotFailure(self, f):
        self.finished = True
        # Now make it look like a success so the failure isn't unhandled
        return {'failure':f}

class WebDatabase:
    '''
    Class that handles the Database of webs for the proxy.

    functions:
        create()
        add_custom_filter(uid, is_black, description, url)
        check_web(url, uid)
        list_filters(uid)
        remove_filter(uid, list_id)

        add_origin(name, uid, description)
        add_url_list(uid, description, listurl)
        add_web(is_origin_new, is_black, uid, category, type,
                orig_name, orig_description, body)
    '''


    def __init__(self, dbpool):
        self.dbpool = dbpool

    def create(self):
        return self.dbpool.runInteraction(self.__create)

    def __create(self, txn):
        txn.execute("CREATE TABLE origin ( " +
                             "id INTEGER PRIMARY KEY, " +
                             "name TEXT, " +
                             "uid TEXT, " +
                             "timestamp INTEGER, " + 
                             "description TEXT, " +
                             "is_black BOOL" +
                         ")")
        print 'created origin table in database'
        txn.execute("CREATE TABLE website ( " +
                             "id INTEGER PRIMARY KEY, " +
                             "is_black BOOL, " +
                             "uid TEXT, " +
                             "origin_id INT NOT NULL CONSTRAINT " +
                                 "origin_id_exists REFERENCES " +
                                 "origin(id) ON DELETE CASCADE, " +
                             "category TEXT, " +
                             "type TEXT, " +
                             "body TEXT" + 
                         ")")
        print 'created website table in database'


    def list_filters(self, uid):
        ret = []
        query = self.dbpool.runQuery("SELECT * FROM Origin WHERE uid='%s'" % uid)

        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            
            for f in qr :
                ret.append([ int(f[0]), str(f[1]), str(f[4]), bool(f[5]) ])

            return ret
        except:
            print "Something goes wrong Listing Filters"
            return ret

    def add_custom_filter(self, uid, is_black, name, description, regex):
        query = self.dbpool.runInteraction(self.__add_custom_filter_cb, uid, is_black, name, description, regex)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Adding Custom Filters"
            return False

    def __add_custom_filter_cb(self, txn, uid, is_black, name, description, regex):
        timestamp = int(time.time())
        if "/" in regex :
            t="url"
            if regex.startswith("http://") :
                body = regex.replace("http://", "")
            elif regex.startswith("https://") :
                body = regex.replace("https://", "")
            else:
                body = regex
            
            description = description + " (url : %s)" % regex
        else:
            t="domain"
            if regex.startswith("http://") :
                body = regex.replace("http://", "")
            elif regex.startswith("https://") :
                body = regex.replace("https://", "")
            else:
                body = regex
            description = description + " (%s)" % regex
            
        sql="INSERT INTO Origin ('name', 'uid', 'timestamp', 'description', 'is_black') VALUES ('%s', '%s', %s, '%s', %s)" % (name, uid, timestamp, description, int(is_black))
        txn.execute(sql)

        txn.execute("SELECT last_insert_rowid()")
        ret = txn.fetchall()

        origin_id = ret[0][0]

        sql="INSERT INTO Website ('is_black', 'uid', 'origin_id', 'category', 'type', 'body') VALUES (%s, '%s', %s, '%s', '%s', '%s')" % (int(is_black), uid, int(origin_id), "manual", t, body)
        txn.execute(sql)

    def remove_filter(self, list_id):
        query = self.dbpool.runInteraction(self.__remove_filter, list_id)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Removing Filters"
            return False

    def __remove_filter(self, txn, list_id):
        txn.execute("DELETE FROM Website WHERE origin_id=%s" % list_id)
        txn.execute("DELETE FROM Origin WHERE id=%s" % list_id)

    def add_dans_guardian_list(self, uid, name, description, list_url):
        description = description + " (%s)" % list_url
        dgi = DansGuardianImporter(self.dbpool, list_url, uid, name, description)
        try:
            ret = dgi.blockOn()
            return ret
        except:
            print "Something goes wrong Importing Dansguardian"
            return False
        

