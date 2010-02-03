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

import gtop

class LinuxSessionFiltering(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.uids_blocked = []
        self.logout_petitions = {}
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)
        
        self.quarterback.connect('block-status', self.__update_cb)
        self.quarterback.connect("update-blocks", self.__update_blocks_cb)

    def start(self):
        pam_deny="auth required pam_listfile.so onerr=succeed item=user sense=deny file=/var/lib/nanny/sessions_blocked"
        os.system('touch /var/lib/nanny/sessions_blocked')
        os.system('sed -i "/^.*nanny\/sessions_blocked.*$/d" /etc/pam.d/gdm')
        os.system('echo %s >> /etc/pam.d/gdm' % pam_deny)
        self.__update_blocks_cb(self.quarterback, self.quarterback.blocks)
        print "Start Linux Session Filtering"
        
    def stop(self):
        os.system('sed -i "/^.*nanny\/sessions_blocked.*$/d" /etc/pam.d/gdm')
        os.system('rm /var/lib/nanny/sessions_blocked')
        os.system('touch /var/lib/nanny/sessions_blocked')
        print "Stop Linux Filtering"

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
                        os.system("echo '%s' >> /var/lib/nanny/sessions_blocked" % uname)
                        #self.__logout_session_if_is_running(user_id)
                        print "blocked session to user '%s'" % uname
                        return
            else:
                if user_id in self.uids_blocked:
                    users = quarterback.usersmanager.get_users()
                    for uid, uname, ufname in users :
                        if str(uid) == user_id :
                            self.uids_blocked.pop(self.uids_blocked.index(user_id))
                            os.system('sed -i "/%s/d" /var/lib/nanny/sessions_blocked' % uname)
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
                    os.system("echo '%s' >> /var/lib/nanny/sessions_blocked" % uname)
                    self.__logout_session_if_is_running(user_id)
                    print "blocked session to user '%s'" % uname
                    return
        
        if block_status == False:
            if user_id in self.uids_blocked:
                users = quarterback.usersmanager.get_users()
                for uid, uname, ufname in users :
                    if str(uid) == user_id :
                        self.uids_blocked.pop(self.uids_blocked.index(user_id))
                        os.system('sed -i "/%s/d" /var/lib/nanny/sessions_blocked' % uname)
                        print "Unblocked session to user '%s'" % uname
            return
        else:
            if user_id in self.uids_blocked :
                return
            
            users = quarterback.usersmanager.get_users()
            for uid, uname, ufname in users :
                if str(uid) == user_id :
                    self.uids_blocked.append(user_id)
                    os.system("echo '%s' >> /var/lib/nanny/sessions_blocked" % uname)
                    self.__logout_session_if_is_running(user_id)
                    print "blocked session to user '%s'" % uname

            return
        
    def __logout_session_if_is_running(self, user_id):
        proclist = gtop.proclist(gtop.PROCLIST_KERN_PROC_UID, int(user_id))
        for proc in proclist:
            if gtop.proc_args(proc)[0] == "x-session-manager" or gtop.proc_args(proc)[0] == "gnome-session":
                users = self.quarterback.usersmanager.get_users()
                for uid, uname, ufname in users :
                    if str(uid) == user_id :
                        if not self.logout_petitions.has_key(user_id):
                            self.logout_petitions[user_id] = 3

                        if self.logout_petitions[user_id] != 0 :
                            print "Sending logout petition to '%s'" % uname
                            cmd='su %s -c "`grep -z DBUS_SESSION_BUS_ADDRESS /proc/%s/environ | sed -e "s:\\r::g"` dbus-send --dest=\'org.gnome.SessionManager\' /org/gnome/SessionManager org.gnome.SessionManager.Logout uint32:0"' % (uname, proc)
                            os.system(cmd)
                            self.logout_petitions[user_id] = self.logout_petitions[user_id] - 1
                            return 
                        else:
                            print "Sending Force logout petition to '%s'" % uname
                            cmd='su %s -c "`grep -z DBUS_SESSION_BUS_ADDRESS /proc/%s/environ | sed -e "s:\\r::g"` dbus-send --dest=\'org.gnome.SessionManager\' /org/gnome/SessionManager org.gnome.SessionManager.Logout uint32:1"' % (uname, proc)
                            os.system(cmd)
                            self.logout_petitions.pop(user_id)
                            return

        if self.logout_petitions.has_key(user_id) :
            self.logout_petitions.pop(user_id)
    
            
