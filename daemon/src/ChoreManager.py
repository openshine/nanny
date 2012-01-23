#!/usr/bin/env python

# Copyright (C) 2009,2010 Junta de Andalucia
# Copyright (C) 2012 Guido Tabbernuk
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
#   Cesar Garcia Tapia <cesar.garcia.tapia at openshine.com>
#   Luis de Bethencourt <luibg at openshine.com>
#   Pablo Vieytes <pvieytes at openshine.com>
#   Guido Tabbernuk <boamaod at gmail.com>
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
import sqlite3

from twisted.enterprise import adbapi

from BlockingDeferred import BlockingDeferred

def on_db_connect(conn):
    conn.execute('PRAGMA foreign_keys=ON')

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

CHORES_DB = os.path.join(NANNY_DAEMON_DATA, "chores.db")
   
class ChoreManager:
    def __init__(self, quarterback):
        self.chores_db = self.__get_chores_db()
        self.quarterback = quarterback

    def __get_chores_db(self):
        path = CHORES_DB
        if os.path.exists(path):
            db = adbapi.ConnectionPool('sqlite3', path,
                                       check_same_thread=False,
                                       cp_openfun=on_db_connect)
        else:
            db = adbapi.ConnectionPool('sqlite3', path,
                                       check_same_thread=False,
                                       cp_openfun=on_db_connect)
            db.runOperation('CREATE TABLE chore_descriptions (id INTEGER PRIMARY KEY, title TEXT, description TEXT, reward INTEGER)')
            db.runOperation('CREATE TABLE chore_status (id INTEGER PRIMARY KEY, chore_id INTEGER, uid TEXT, contracted INTEGER, \
                            finished INTEGER, FOREIGN KEY(chore_id) REFERENCES chore_descriptions(id) ON DELETE CASCADE ON UPDATE CASCADE)')
            print "Created chores db"

        return db

    # Chore descriptions to be used assigning chores to users

    def add_chore_description(self, title, description, reward):
        sql_query = 'INSERT INTO chore_descriptions ("title", "description", "reward") VALUES ("%s", "%s", "%s")' % (title, description, reward)
        query = self.chores_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Adding Chore Description"
            return False

    def list_chore_descriptions(self, desc_id):
        qstr = "SELECT * FROM chore_descriptions"
        if desc_id != -1:
            qstr = qstr + ' WHERE id = "%s"' % (desc_id)
        qstr = qstr + ' ORDER BY title ASC'
        query = self.chores_db.runQuery(qstr)
        block_d = BlockingDeferred(query)
        ret = []
        
        try:
            qr = block_d.blockOn()
            
            for f in qr :
                ret.append([ int(f[0]), unicode(f[1]), unicode(f[2]), int(f[3]) ])

            return ret
        except:
            print "Something goes wrong Listing Chore Description"
            return ret

    def remove_chore_description(self, list_id):
        query = self.chores_db.runQuery('DELETE FROM chore_descriptions WHERE id="%s"' % int(list_id))
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            
            return True
        except:
            print "Something goes wrong Removing Chore Description"
            return False

    def update_chore_description(self, list_id, title, description, reward):
        sql_query = 'UPDATE chore_descriptions SET title="%s", description="%s", reward="%s" WHERE id=%s' % (title,
                                                                                                      description,
                                                                                                      reward,
                                                                                                      int(list_id))
        query = self.chores_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Updating Chore Description"
            return False
            
    # Real chores for real users

    def add_chore(self, chore_id, uid):
        sql_query = 'INSERT INTO chore_status ("uid", "chore_id", "contracted", "finished") VALUES ("%s", "%s", "-1", "-1")' % (uid, chore_id)
        query = self.chores_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Adding Chore"
            return False

    def get_contracted_chores_count(self, uid):
        qstr = 'SELECT COUNT(*) FROM chore_status JOIN chore_descriptions ON chore_id=chore_descriptions.id WHERE uid="%s" AND contracted != "-1" AND finished == "-1"' % (str(uid))
        query = self.chores_db.runQuery(qstr)
        block_d = BlockingDeferred(query)
       
        try:
            qr = block_d.blockOn()
            
            return qr[0][0]
        except:
            print "Something goes wrong getting Contracted Chores count"
            return -1
    
        
    def list_chores(self, uid, available, contracted, finished):
        """Available chores are the chores not yet contracted."""
        
        qstr = 'SELECT chore_status.id, chore_id, uid, reward, contracted, finished, title, description FROM chore_status JOIN chore_descriptions ON chore_id=chore_descriptions.id WHERE uid="%s"' % (str(uid))
        if available:
            qstr = qstr + ' AND contracted = "-1"'
        if contracted:
            qstr = qstr + ' AND contracted != "-1" AND finished == "-1"'
        if finished:
            qstr = qstr + ' AND finished != "-1"'
        if available:
            qstr = qstr + ' ORDER BY title ASC'
        if contracted:
            qstr = qstr + ' ORDER BY contracted ASC'
        if finished:
            qstr = qstr + ' ORDER BY finished DESC'
        query = self.chores_db.runQuery(qstr)
        block_d = BlockingDeferred(query)
        ret = []
        
        try:
            qr = block_d.blockOn()
            
            for f in qr :
                ret.append([ int(f[0]), int(f[1]), unicode(f[2]), int(f[3]), int(f[4]), int(f[5]), unicode(f[6]), unicode(f[7]) ])

            return ret
        except:
            print "Something goes wrong Listing Chore"
            return ret

    def remove_chore(self, list_id):
        query = self.chores_db.runQuery('DELETE FROM chore_status WHERE id=%s' % int(list_id))
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Removing Chore"
            return False

    def update_chore(self, list_id, chore_id, uid, contracted, finished):
        sql_query = 'UPDATE chore_status SET chore_id="%s", uid="%s", contracted="%s", finished="%s" WHERE id=%s' % (
                                                                                                      chore_id,
                                                                                                      uid,
                                                                                                      contracted,
                                                                                                      finished,
                                                                                                      int(list_id))

        query = self.chores_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Updating Chore"
            return False

    def get_activated_chore_reward(self, list_id):
        sql_query = 'SELECT reward FROM chore_status JOIN chore_descriptions on chore_descriptions.id=chore_status.chore_id WHERE chore_status.id="%s"' % (
                                                                          int(list_id))

        query = self.chores_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        
        try:
            qr = block_d.blockOn()
            
            for f in qr :
                return int(f[0])

            print "Something goes wrong finding our reward for the chore (broken database?)"
            return -1
        except:
            print "Something goes wrong finding our reward for the chore"
            return -1


    def contract_chore(self, list_id, uid, contracted):
        sql_query = 'UPDATE chore_status SET contracted="%s" WHERE id="%s"' % (
                                                                          contracted,
                                                                          int(list_id))
        query = self.chores_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
        except:
            print "Something goes wrong Contracting Chore"
            return False

        print "Chore contracted"

        self.quarterback.add_available_time(uid, 0, self.get_activated_chore_reward(int(list_id)))
        
        return True

    def finish_chore(self, list_id, finished):
        sql_query = 'UPDATE chore_status SET finished="%s" WHERE id="%s"' % (
                                                                          finished,
                                                                          int(list_id))
        query = self.chores_db.runQuery(sql_query)
        block_d = BlockingDeferred(query)
        try:
            qr = block_d.blockOn()
            return True
        except:
            print "Something goes wrong Updating Chore"
            return False




