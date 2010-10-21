#!/usr/bin/env python

# Copyright (C) 2009,2010 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
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

from twisted.internet import threads, reactor, defer
from twisted.python import failure
import Pyro.core
import threading
import time
import Queue

from threading import Semaphore


def PyroBlockingCallFromThread(reactor, f, *a, **kw):
    queue = Queue.Queue()
    se = Semaphore(1)

    def _callFromThread():
        if se._Semaphore__value == 1 :
            se.acquire()
        else:
            return
        
        result = defer.maybeDeferred(f, *a, **kw)
        result.addBoth(queue.put)

    reactor.callFromThread(_callFromThread)
    result = queue.get()
    if isinstance(result, failure.Failure):
        result.raiseException()
    return result

class OrgGnomeNanny(Pyro.core.ObjBase):
    def __init__(self, quarterback):
        Pyro.core.ObjBase.__init__(self)
        self.quarterback = quarterback
        self.quarterback.connect('update-users-info', self.__UpdateUsersInfo_cb)
        self.events = []

    def IsUnLocked(self):
        return False

    def UnLock(self):
        return True

    def ListUsers(self):
        return PyroBlockingCallFromThread(reactor, self.quarterback.usersmanager.get_users)

    def SetBlocks(self, user_id, app_id, blocks):
        PyroBlockingCallFromThread(reactor, self.quarterback.set_blocks, str(user_id), int(app_id), blocks)
        return True

    def GetBlocks(self, user_id, app_id) :
        return PyroBlockingCallFromThread(reactor, self.quarterback.get_blocks, user_id, app_id)

    def SetActiveWCF(self, active, uid):
        PyroBlockingCallFromThread(reactor, self.quarterback.set_wcf, bool(active), str(uid))

    def ListWCF(self):
        return PyroBlockingCallFromThread(reactor, self.quarterback.list_wcf_uids)

    def SetMaxUseTime(self, user_id, app_id, mins):
        PyroBlockingCallFromThread(reactor, self.quarterback.set_max_use_time, str(user_id), int(app_id), int(mins))

    def GetMaxUseTime(self, user_id, app_id):
        return PyroBlockingCallFromThread(reactor, self.quarterback.get_max_use_time , user_id, app_id)
    
    # FIXME : Singal
    #def UpdateUsersInfo(self):
    #    pass

    def __UpdateUsersInfo_cb(self, quarterback):
        #self.UpdateUsersInfo()
        self.events.append((time.time(), "update-users-info", None))
        self.__clear_old_events()

    def __clear_old_events(self):
        pass

    def GetEventsFromTimeStamp(self, timestamp):
        ret = []
        for event in self.events :
            if event[0] > timestamp :
                ret.append(event)
        return ret 


class OrgGnomeNannyNotification(Pyro.core.ObjBase):
    def __init__(self, quarterback):
        Pyro.core.ObjBase.__init__(self)
        self.quarterback = quarterback
        self.quarterback.connect('block-status', self.__UserNotification_cb)
        self.events = []

    # FIXME : Singal
    #def UserNotification(self, block_status, user_id, app_id, next_change, available_time):
    #    pass

    def __UserNotification_cb(self, quarterback, block_status, user_id, app_id, next_change, available_time):
        #self.UserNotification(block_status, user_id, app_id, next_change, available_time)
        self.events.append((time.time(), "user-notification", 
                            (block_status, user_id, app_id, next_change, available_time)))
        self.__clear_old_events()

    def __clear_old_events(self):
        pass

    def GetEventsFromTimeStamp(self, timestamp):
        ret = []
        for event in self.events :
            if event[0] > timestamp :
                ret.append(event)
        return ret 
    
class OrgGnomeNannyWebDatabase(Pyro.core.ObjBase):
    def __init__(self, quarterback):
        Pyro.core.ObjBase.__init__(self)
        self.quarterback = quarterback
        
    def AddCustomFilter(self, uid, is_black, name, description, regex):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.add_custom_filter, str(uid), bool(is_black), unicode(name),
                                              unicode(description), unicode(regex))

    def ListCustomFilters(self, uid):
        ret = PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.list_custom_filters, int(uid))
        return ret

    def RemoveCustomFilter(self, list_id):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.remove_custom_filter, int(list_id))

    def UpdateCustomFilter(self, list_id, name, description, regex):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.update_custom_filter, int(list_id),
                                              unicode(name),
                                              unicode(description),
                                              unicode(regex))
    
    def AddPkgFilter(self, path):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.add_pkg_filter, str(path))
    
    def RemovePkgFilter(self, pkg_id):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.remove_pkg_filter, str(pkg_id))

    def UpdatePkgFilter(self, pkg_id, new_db_path):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.update_pkg_filter, str(pkg_id), str (new_db_path))

    def ListPkgFilters(self):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.list_pkg_filter)

    def GetPkgFilterMetadata(self, pkg_id):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.get_pkg_filter_metadata, str(pkg_id))

    def SetPkgFilterMetadata(self, pkg_id, name, description):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.set_pkg_filter_metadata, str(pkg_id), unicode(name), unicode(description))

    def GetPkgFilterUserCategories(self, pkg_id, uid):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.get_pkg_filter_user_categories, unicode(pkg_id),
                                              str(uid)
                                              )

    def SetPkgFilterUserCategories(self, pkg_id, uid, list_categories):
        list_c = []
        for x in list_categories :
            list_c.append(unicode(x))
            
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.set_pkg_filter_user_categories, unicode(pkg_id),
                                              str(uid),
                                              list_c)

    def CheckDomain(self, uid, domain):
        return PyroBlockingCallFromThread(reactor, self.quarterback.filter_manager.check_domain, uid, domain)

    def AddDansGuardianList(self, uid, name, description, list_url):
        return PyroBlockingCallFromThread(reactor, self.quarterback.webcontent_filter.webdb.add_dans_guardian_list, str(uid),
                                              unicode(name),
                                              unicode(description),
                                              unicode(list_url))
    

def inThread(quarterback):
    Pyro.core.initServer()
    daemon=Pyro.core.Daemon()
    daemon.host = "localhost"

    uries = []
    uries.append(daemon.connect(OrgGnomeNanny(quarterback),"org.gnome.Nanny"))
    uries.append(daemon.connect(OrgGnomeNannyNotification(quarterback),"org.gnome.Nanny.Notification"))
    uries.append(daemon.connect(OrgGnomeNannyWebDatabase(quarterback),"org.gnome.Nanny.WebDatabase"))

    print "The daemon runs on port:",daemon.port
    for uri in uries :
        print "   The object's uri is:",uri
    reactor.addSystemEventTrigger("before", "shutdown", daemon.shutdown)
    daemon.requestLoop()

def start_pyro_bus(quarterback):
    reactor.callInThread(inThread, quarterback)


