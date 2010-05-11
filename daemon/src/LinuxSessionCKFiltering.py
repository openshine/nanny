#!/usr/bin/env python
#
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

import gobject
import os
import dbus

from twisted.internet import reactor, threads
from time import localtime, strftime

import gtop

class LinuxSessionCKFiltering(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback

        self.uids_blocked = []
        self.desktop_blocked = []
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)
        
        self.quarterback.connect('block-status', self.__update_cb)
        self.quarterback.connect("update-blocks", self.__update_blocks_cb)

    def start(self):
        self.__update_blocks_cb(self.quarterback, self.quarterback.blocks)
        print "Start Linux Session ConsoleKit Filtering"

    def stop(self):
        print "Stop Linux Session ConsoleKit Filtering"

    def __update_blocks_cb(self, quarterback, blocks):
        for user_id in blocks.keys() :
            if not blocks[user_id].has_key(0) :
                continue

            block_status, next_change = quarterback.is_blocked(user_id, 0)
            if quarterback.get_available_time(user_id, 0) == 0 or block_status == True:
                if user_id in self.uids_blocked :
                    return

                users = quarterback.usersmanager.get_users()
                for uid, uname, ufname in users :
                    if str(uid) == user_id :
                        self.uids_blocked.append(user_id)
                        print "blocked session to user '%s'" % uname
                        return
            else:
                if user_id in self.uids_blocked:
                    users = quarterback.usersmanager.get_users()
                    for uid, uname, ufname in users :
                        if str(uid) == user_id :
                            self.uids_blocked.pop(self.uids_blocked.index(user_id))
                            print "Unblocked session to user '%s'" % uname


    def __update_cb(self, quarterback, block_status, user_id, app_id, next_change, available_time):
        if app_id != 0 :
            return

        if block_status == True or available_time == 0 :
            if user_id in self.uids_blocked :
                self.__logout_session_if_is_running(user_id)
        
        if available_time == 0 :
            if user_id in self.uids_blocked :
                return

            users = quarterback.usersmanager.get_users()
            for uid, uname, ufname in users :
                if str(uid) == user_id :
                    self.uids_blocked.append(user_id)
                    self.__logout_session_if_is_running(user_id)
                    print "blocked session to user '%s'" % uname
                    return
        
        if block_status == False:
            if user_id in self.uids_blocked:
                users = quarterback.usersmanager.get_users()
                for uid, uname, ufname in users :
                    if str(uid) == user_id :
                        self.uids_blocked.pop(self.uids_blocked.index(user_id))
                        print "Unblocked session to user '%s'" % uname
            return
        else:
            if user_id in self.uids_blocked :
                return
            
            users = quarterback.usersmanager.get_users()
            for uid, uname, ufname in users :
                if str(uid) == user_id :
                    self.uids_blocked.append(user_id)
                    self.__logout_session_if_is_running(user_id)
                    print "blocked session to user '%s'" % uname

            return
        
    def __logout_session_if_is_running(self, user_id):
        try:
            d = dbus.SystemBus()
            manager = dbus.Interface(d.get_object("org.freedesktop.ConsoleKit", "/org/freedesktop/ConsoleKit/Manager"), 
                                     "org.freedesktop.ConsoleKit.Manager")
            sessions = manager.GetSessionsForUnixUser(int(user_id))
            for session_name in sessions :
                session = dbus.Interface(d.get_object("org.freedesktop.ConsoleKit", session_name),
                                         "org.freedesktop.ConsoleKit.Session")
                x11_display = session.GetX11Display()
                if x11_display == "":
                    continue

                if session_name not in self.desktop_blocked :
                    self.desktop_blocked.append(session_name)
                    t = threads.deferToThread(self.__launch_desktop_blocker, session_name, user_id, x11_display)
                    t.addCallback(self.__result_of_desktop_blocker)
        except:
            print "Crash __logout_session_if_is_running()"
            
    def __launch_desktop_blocker(self, session_name, user_id, x11_display):
        print "Launch desktop-blocker to '%s'" % session_name
        proclist = gtop.proclist(gtop.PROCLIST_KERN_PROC_UID, int(user_id))

        if len(proclist) > 0 :
            from subprocess import Popen, PIPE

            lang_var = Popen('cat /proc/%s/environ | tr "\\000" "\\n" | grep ^LANG= ' % proclist[0] , shell=True, stdout=PIPE).stdout.readline().strip("\n")
            ret = os.system('DISPLAY=%s %s nanny-desktop-blocker' % (x11_display, lang_var))
        else:
            ret = os.system('DISPLAY=%s nanny-desktop-blocker' % (x11_display))

        return session_name, user_id, ret

    def __result_of_desktop_blocker(self, result):
        session_name = result[0]
        user_id = result[1]
        ret_code = result[2]
        print "Results desktop-blocker to '%s' (%s)" % (session_name, ret_code)
        if ret_code == 0:
            self.__remote_close_session(user_id)

        if session_name in self.desktop_blocked :
            self.desktop_blocked.pop(self.desktop_blocked.index(session_name))
    
    def __remote_close_session(self, user_id):
        proclist = gtop.proclist(gtop.PROCLIST_KERN_PROC_UID, int(user_id))
        for proc in proclist:
            if gtop.proc_args(proc)[0] == "x-session-manager" or gtop.proc_args(proc)[0] == "gnome-session":
                users = self.quarterback.usersmanager.get_users()
                for uid, uname, ufname in users :
                    if str(uid) == user_id :
                        print "Sending Force logout petition to '%s'" % uname
                        cmd='su %s -c "`grep -z DBUS_SESSION_BUS_ADDRESS /proc/%s/environ | sed -e "s:\\r::g"` dbus-send --dest=\'org.gnome.SessionManager\' /org/gnome/SessionManager org.gnome.SessionManager.Logout uint32:1"' % (uname, proc)
                        os.system(cmd)
                        return
        
            
    
        

