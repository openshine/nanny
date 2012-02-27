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

import gobject
import os
import sys

import copy
import pickle, csv
import time
from datetime import datetime, timedelta

if os.name == "posix" :
    from LinuxFiltering import LinuxFiltering as FirewallFilter
    from LinuxWebContentFiltering import LinuxWebContentFiltering as WebContentFilter
    from LinuxUsersManager import LinuxUsersManager as UsersManager
    from LinuxSessionFiltering import LinuxSessionFiltering as SessionFilter
    from FilterManager import FilterManager as FilterManager
    from ChoreManager import ChoreManager as ChoreManager
    from Chrono import Chrono
elif os.name == "nt" :
    from Win32Filtering import Win32Filtering as FirewallFilter
    from Win32WebContentFiltering import Win32WebContentFiltering as WebContentFilter
    from Win32UsersManager import Win32UsersManager as UsersManager
    from Win32SessionFiltering import Win32SessionFiltering as SessionFilter
    from FilterManager import FilterManager as FilterManager
    from ChoreManager import ChoreManager as ChoreManager
    from Win32Chrono import Win32Chrono as Chrono
    from Win32Top import Win32Top


def GetInHM(m):
    seconds = m*60
    hours = seconds / 3600
    seconds -= 3600*hours
    minutes = seconds / 60
    return "%02d:%02d" % (hours, minutes)


if os.name == "posix" :
    BLOCK_DB = "/var/lib/nanny/nanny-block.db"
    ARCHIVE_DB = "/var/lib/nanny/nanny-archive.db"
elif os.name == "nt" :
    if not hasattr(sys, "frozen") :
        file_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for x in range(6):
            file_dir = os.path.dirname(file_dir)
        root_path = file_dir
        
        BLOCK_DB = os.path.join(root_path, "var", "lib", "nanny", "nanny-block.db")
        ARCHIVE_DB = os.path.join(root_path, "var", "lib", "nanny", "nanny-archive.db")
    else:
        BLOCK_DB = os.path.join(os.environ["ALLUSERSPROFILE"], "Gnome", "nanny", "nanny-block.db")
        ARCHIVE_DB = os.path.join(os.environ["ALLUSERSPROFILE"], "Gnome", "nanny", "nanny-archive.db")


WEEKDAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]

class QuarterBack(gobject.GObject) :
    __gsignals__ = {
        'block-status' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)),
        'update-blocks' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_PYOBJECT,)),
        'add-wcf-to-uid' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                       (gobject.TYPE_PYOBJECT,)),
        'remove-wcf-to-uid' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                          (gobject.TYPE_PYOBJECT,)),
        'update-users-info' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                               ()),
        }

    def __init__(self, app) :
        gobject.GObject.__init__(self)
        self.app = app
        self.blocks = {}
        self.wcf_uid_list = []
        self.chore_settings = {}
        self.chrono_times = {}
        self.chrono_day = (datetime.today() - datetime.utcfromtimestamp(0)).days
        
        if not os.path.exists(BLOCK_DB) :
            try:
                os.makedirs(os.path.dirname(BLOCK_DB))
            except:
                pass
        else:
            try:
                db = open(BLOCK_DB, 'rb')
                p = pickle.load(db)
                self.blocks = p[0]
                self.chore_settings = p[1]
                self.wcf_uid_list = p[2]
                self.chrono_times = p[3]
                self.chrono_day = p[4]
                
                db.close()
            except:
                print "Something wrong unpickling, trying older format (2.31.1)..."
                
                # old format (2.31.1) support
                try:
                    db = open(BLOCK_DB, 'rb')
                    p = pickle.load(db)
                    self.blocks = p[0]
                    self.wcf_uid_list = p[1]
                    self.chrono_times = p[2]
                    self.chrono_day = p[3]
                    
                    db.close()
                except:
                    print "No success, something just went wrong unpickling"

            # more old format (2.31.1) support
            for t in self.chrono_times:
                announced = False
                for c in self.chrono_times[t]:
                    if len(self.chrono_times[t][c].items()) == 2: # 2.31.1 had 2 fields
                        if not announced:
                            print 'Old format (2.31.1) support: adding extra fields to user', t
                            announced = True
                        self.chrono_times[t][c]["extra_time"] = 0
                        self.chrono_times[t][c]["mercy_count"] = 0
                        self.chrono_times[t][c]["force_close"] = 0
                        self.chrono_times[t][c]["last_active"] = -1

        self.__next_update_info = None
        self.usersmanager = UsersManager()
        if os.name == "nt" :
             self.win32top = Win32Top(self)
        self.chrono = Chrono(self)
        
        self.firewall_filter = FirewallFilter(self)
        self.filter_manager = FilterManager(self)
        self.chore_manager = ChoreManager(self)
        self.webcontent_filter = WebContentFilter(self, app)
        self.session_filter = SessionFilter(self)
        
        gobject.timeout_add(1000, self.__polling_cb)

    def __polling_cb(self):
        self.__check_users_info()
        
        if  self.__next_update_info != None :
            if self.__next_update_info != time.localtime().tm_min :
                return True

            if self.chrono_day != (datetime.today() - datetime.utcfromtimestamp(0)).days:
                self.__add_to_archive()
                self.new_chrono_day()

        self.__refresh_info()
        self.__next_update_info = (time.localtime().tm_min + 1) % 60
        return True

    def __check_users_info(self):
        some_users_info_changed = False
        if not self.usersmanager.has_changes() :
            return
        
        users = self.usersmanager.get_users()
        for user_id, user_name, user_fullname in users :
            if not self.blocks.has_key(user_id) :
                self.blocks[user_id] = {0: [], 1: [], 2: [], 3: []}
                some_users_info_changed = True
            if not self.chrono_times.has_key(user_id) :
                self.chrono_times[user_id] = self.__new_user_chrono_times()
                some_users_info_changed = True
            if not self.chore_settings.has_key(user_id) :
                self.chore_settings[user_id] = [True, 5] # defaults to: can use chores, max 5 unfinished
                some_users_info_changed = True

        # remove deleted users from lists
        #
        
        blocks_uids = self.blocks.keys()
        for user_id, user_name, user_fullname in users :
            if self.blocks.has_key(user_id) :
                blocks_uids.pop(blocks_uids.index(user_id))
        for uid in blocks_uids :
            self.blocks.pop(uid)
            some_users_info_changed = True

        chrono_uids = self.chrono_times.keys()
        for user_id, user_name, user_fullname in users :
            if self.chrono_times.has_key(user_id) :
                chrono_uids.pop(chrono_uids.index(user_id))
        for uid in chrono_uids :
            self.chrono_times.pop(uid)
            some_users_info_changed = True

        chore_uids = self.chore_settings.keys()
        for user_id, user_name, user_fullname in users :
            if self.chore_settings.has_key(user_id) :
                chore_uids.pop(chore_uids.index(user_id))
        for uid in chore_uids :
            self.chore_settings.pop(uid)
            some_users_info_changed = True

        wcf_uids = copy.copy(self.wcf_uid_list)
        for user_id, user_name, user_fullname in users :
            if user_id in self.wcf_uid_list :
                wcf_uids.pop(wcf_uids.index(user_id))

        for uid in wcf_uids :
            self.wcf_uid_list.pop(self.wcf_uid_list.index(uid))
            self.emit("remove-wcf-to-uid", uid)
            some_users_info_changed = True

        if some_users_info_changed == True :
            self.__save()
            print "Update Users Info"
            self.emit("update-users-info")
            self.__refresh_info()

    def __refresh_info(self):
        for user_id in self.blocks.keys() :
            for app_id in self.blocks[user_id] :
                block_status, next_change = self.is_blocked(user_id, app_id)
                available_time = self.get_available_time(user_id, app_id)
                self.emit("block-status", block_status, user_id, app_id, next_change, available_time, self.chrono_times[user_id][app_id]["last_active"] + 1 >= int(time.time()/60))

    def __get_min_block_status(self, user_id, app_id, min) :
        for block in self.blocks[user_id][app_id]:
            l, r = block
            if l <= min <= r :
                return True
        return False

    def __add_to_archive(self):
        """Appends usage data of the (previous) day to archive"""
        
        output = open(ARCHIVE_DB, 'a')
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

        v=[]
        for t in self.chrono_times:
            z=[self.chrono_day, t]
            for c in self.chrono_times[t]:
                for s in self.chrono_times[t][c]:
                    z.append(self.chrono_times[t][c][s])
            v.append(z)

        writer.writerows(v)
        output.close()


    def __save(self):        
        output = open(BLOCK_DB, 'wb')
        p = [self.blocks, self.chore_settings, self.wcf_uid_list,
             self.chrono_times, self.chrono_day]
        pickle.dump(p, output)
        output.close()

    def __new_user_chrono_times(self):
        user ={0: {"max_use": 0, "used_time": 0, "extra_time": 0, "mercy_count": 0, "force_close": 0, "last_active": -1},
               1: {"max_use": 0, "used_time": 0, "extra_time": 0, "mercy_count": 0, "force_close": 0, "last_active": -1},
               2: {"max_use": 0, "used_time": 0, "extra_time": 0, "mercy_count": 0, "force_close": 0, "last_active": -1},
               3: {"max_use": 0, "used_time": 0, "extra_time": 0, "mercy_count": 0, "force_close": 0, "last_active": -1}}
        return user

    def is_allowed_to_use(self, user_id, app_id):
        available_time = self.get_available_time(user_id, app_id)
        is_blocked = self.is_blocked(user_id, app_id)[0]
        
        return not is_blocked and available_time != 0

    def is_forced_to_close(self, userid, appid):
        if not self.chrono_times.has_key(userid):
            return False
        if not self.chrono_times[userid].has_key(appid):
            return False

        return bool(self.chrono_times[userid][appid]["force_close"])

    def set_forced_to_close(self, userid, appid, state):
        self.chrono_times[userid][appid]["force_close"] = int(state)
        self.__save()

    def is_chore_available(self, user_id):
        count = self.chore_manager.get_contracted_chores_count(user_id)
        limit = self.chore_settings[user_id][1]
        chores_available = len(self.chore_manager.list_chores(user_id, available=True, contracted=False, finished=False))
        return count < limit and chores_available > 0

    def is_blocked(self, user_id, app_id, date_time=None):
        block_status = False
        next_block = -1
        
        if not self.blocks.has_key(user_id) :
            return block_status, next_block

        if not self.blocks[user_id].has_key(app_id) :
            return block_status, next_block

        if date_time == None:
            t = time.localtime()
            h = t.tm_hour
            m = t.tm_min
            wt = [1,2,3,4,5,6,0]
            w = wt[t.tm_wday]
        else:
            h = date_time.hour
            m = date_time.minute
            w = date_time.isoweekday()

        atime = int(w)*24*60 + int(h)*60 + int(m)

        block_status = self.__get_min_block_status(user_id, app_id, atime)

        week_m_list = range(atime+1, 24*60*7) + range(0, atime+1)

        for m in week_m_list :
            m_block_status = self.__get_min_block_status(user_id, app_id, m)
            if m_block_status != block_status :
                if m > atime :
                    next_block = m - atime
                else:
                    next_block = (24*60*7 - atime) + m

                if block_status == True :
                    if next_block - 1 == 0 :
                        d = datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min) + timedelta(minutes=1)
                        tb , tnb = self.is_blocked(user_id, app_id, d)
                        return not block_status, tnb + 1
                    return block_status, next_block - 1 
                else:
                    return block_status, next_block

        return block_status, next_block

                
    def get_block_status_by_uid(self, user_id):
        if user_id not in self.blocks.keys():
            return {}
        
        ret = {}
        for app_id in self.blocks[user_id] :
            block_status, next_change = self.is_blocked(user_id, app_id)
            available_time = self.get_available_time(user_id, app_id)
            ret[app_id] = [block_status, next_change, available_time]
            
        return ret

                    
    def set_blocks(self, user_id, app_id, data):
    
        if not self.blocks.has_key(user_id) :
            self.blocks[user_id] = {} 

        if not self.blocks[user_id].has_key(app_id) :
             self.blocks[user_id][app_id] = []

        if len(data) == 0:
            self.blocks[user_id][app_id] = []
            self.__save()
            self.emit("update-blocks", self.blocks)
            return

        block_sets = []

        for key in data.keys() :
            try:
                key_index = WEEKDAYS.index(key.lower())
            except:
                continue

            for init_time, end_time in data[key] :
                ih,im = init_time.split(":")
                eh,em = end_time.split(":")

                if 0 <= int(ih) <= int(eh) <= 24 and 0 <= int(im) <= 59 and 0 <= int(em) <= 59 :
                    itime = (key_index * 24 * 60) + int(ih)*60 + int(im)
                    etime = (key_index * 24 * 60) + int(eh)*60 + int(em)
                    block_sets.append(set(range(itime, etime+1)))
                else:
                    continue
        
        new_block_sets = []
        
        while True :
            if len(block_sets) <= 1 :
                new_block_sets.append(block_sets.pop(0))
                break
            else :
                if block_sets[0].isdisjoint(block_sets[1]) :
                    new_block_sets.append(block_sets.pop(0))
                else:
                    a = block_sets.pop(0)
                    b = block_sets.pop(0)
                    aub = a.union(b)
                    block_sets.insert(0, aub)

        ret = []
        for bs in new_block_sets :
            bs_list = list(bs)
            bs_list.sort()
            
            ret.append((bs_list[0], bs_list[-1]))

        ret.sort()
        self.blocks[user_id][app_id] = ret
        self.__save()
        self.emit("update-blocks", self.blocks)
        self.__refresh_info()

    def get_blocks(self, user_id, app_id):
        if not self.blocks.has_key(user_id) :
            return [] 

        if not self.blocks[user_id].has_key(app_id) :
            return []

        ret = {}

        for i_time, e_time in self.blocks[user_id][app_id] :
            i_index = i_time / (24*60)
            e_index = e_time / (24*60)

            if i_index == e_index :
                if not ret.has_key(WEEKDAYS[i_index]) :
                    ret[WEEKDAYS[i_index]] = []

                ret[WEEKDAYS[i_index]].append(( GetInHM(i_time%(24*60)), GetInHM(e_time%(24*60)) ))

        return ret

    def set_wcf (self, active, uid):
        if active == True :
            if uid not in self.wcf_uid_list :
                self.wcf_uid_list.append(uid)
                self.__save()
                self.emit("add-wcf-to-uid", uid)
        else:
            if uid in self.wcf_uid_list :
                self.wcf_uid_list.pop(self.wcf_uid_list.index(uid))
                self.__save()
                self.emit("remove-wcf-to-uid", uid)

    def list_wcf_uids (self):
        return self.wcf_uid_list

    def set_chore_settings (self, uid, active, limit):
            self.chore_settings[uid] = [active, limit]
            self.__save()

    def get_chore_settings (self, uid):
        return self.chore_settings[uid]

    def get_max_use_time(self, userid, appid):
        if not self.chrono_times.has_key(userid):
            return 0
        if not self.chrono_times[userid].has_key(appid):
            return 0

        return self.chrono_times[userid][appid]["max_use"]

    def set_max_use_time(self, userid, appid, mins):
        if not self.chrono_times.has_key(userid):
            new_user = self.__new_user_chrono_times()
            self.chrono_times[userid] = new_user

        if not self.chrono_times[userid].has_key(appid):
            new_app = {"max_use": 0, "used_time": 0, "extra_time": 0, "mercy_count": 0, "force_close": 0, "last_active": -1}
            self.chrono_times[userid][appid] = new_app

        self.chrono_times[userid][appid]["max_use"] = mins
        self.__save()

    def add_available_time(self, userid, appid, mins):
        if self.chrono_times.has_key(userid):
            if self.chrono_times[userid].has_key(appid):
                    self.chrono_times[userid][appid]["extra_time"] += mins
        self.__save()

    def get_available_time(self, userid, appid):
        if not self.chrono_times.has_key(userid):
            return -1
        if not self.chrono_times[userid].has_key(appid):
            return -1

        used_time = self.chrono_times[userid][appid]["used_time"]
        extra_time = self.chrono_times[userid][appid]["extra_time"]
        max_use = self.chrono_times[userid][appid]["max_use"]
        
        if max_use == 0:
            return -1

        if max_use + extra_time - used_time < 0 :
            return 0
        
        return max_use + extra_time - used_time 

    def take_mercy(self, userid, appid):
        self.chrono_times[userid][appid]["mercy_count"] += 1
        self.__save()
        
    def subtract_time(self, userid, appid, mins=1):
        if self.chrono_times.has_key(userid):
            if self.chrono_times[userid].has_key(appid):
                self.chrono_times[userid][appid]["last_active"] = int(time.time()/60)
                if self.get_available_time(userid, appid) != 0:
                    self.chrono_times[userid][appid]["used_time"] += mins
                    print "Substract time (%s, %s) = %s" % (userid, appid, 
                                                        self.chrono_times[userid][appid]["used_time"])
                    self.__save()

    def new_chrono_day(self):
        self.chrono_day = (datetime.today() - datetime.utcfromtimestamp(0)).days

        for user_id in self.chrono_times.keys():
            for app_id in self.chrono_times[user_id]:
                self.chrono_times[user_id][app_id]["used_time"] = 0
                self.chrono_times[user_id][app_id]["extra_time"] = 0
                self.chrono_times[user_id][app_id]["mercy_count"] = 0
                
        self.__save()




gobject.type_register(QuarterBack)

def b_cb(obj, bs, user_id, app_id, next_change):
    print "[%s] (app_type:%s) -> Blocked = %s, time = %s, next_change=%s %s" % (user_id, app_id,
                                                                                bs,
                                                                                time.localtime()[4],
                                                                                WEEKDAYS[next_change/(24*60)],
                                                                                GetInHM(next_change%(24*60))
                                                                                )


if __name__ == '__main__':
    from pprint import pprint
    q = QuarterBack()
    q.connect("block-status", b_cb)
    # a{sa(ss)}
    data = { "sun" : [("18:00", "19:00"), ("15:20", "23:59")],
             "mon" : [("00:00", "19:00"), ("19:01","20:00")]
             }
    pprint (data)
    print "-------------------------------------"
    q.set_blocks("1001",0, data)
    pprint (q.blocks)

    print "--------------------------------------"
    pprint(q.get_blocks("1001", 0))
    
    print "--------------------------------------"
    
    gobject.MainLoop().run()
