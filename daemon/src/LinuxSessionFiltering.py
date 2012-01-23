#!/usr/bin/env python
#
# Copyright (C) 2009,2010,2011 Junta de Andalucia
# Copyright (C) 2012 Guido Tabbernuk
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
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
import dbus

from twisted.internet import reactor, threads

from subprocess import Popen, PIPE
import time

import gtop

(
SESSION_APPID,
WEB_APPID,
MAIL_APPID,
IM_APPID) = range(4)

class LinuxSessionBlocker(gobject.GObject) :
    def __init__(self, quarterback, session_blocker="nanny-desktop-blocker"):
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.sb = session_blocker
        self.block_status = []

    def is_user_blocked(self, user_id):
        if user_id in self.block_status:
            return True
        else:
            return False

    def blocker_terminate_from_thread(self, user_id, ret):
        print "[LinuxSessionFiltering] self.blocker_terminate_from_thread %s %s" % (user_id, ret)
        if ret == 0:
            gobject.timeout_add(5000, self.__remove_block_status, user_id)
        else:
            print "[LinuxSessionFiltering] User or other try to kill blocker :)"
            gobject.timeout_add(5000, self.__launch_blocker_to_badboy, user_id)
            

    def set_block(self, user_id, block_status):
        if block_status == True:
            if user_id not in self.block_status :
                self.__launch_blocker(user_id)
        else:
            try:
                self.block_status.pop(self.block_status.index(user_id))
            except:
                pass

    def __remove_block_status(self, user_id):
        print "[LinuxSessionFiltering] Remove block status to user_id :  %s" % (user_id)
        self.block_status.pop(self.block_status.index(user_id))
        return False

    def __launch_blocker_to_badboy(self, user_id):
        x11_display = self.__get_user_session_display(user_id)
        if x11_display != None :
            user_name = self.quarterback.usersmanager.get_username_by_uid(user_id)
            reactor.callInThread(self.__launch_blocker_thread, user_id, user_name, x11_display, self)
        else:
            self.block_status.pop(self.block_status.index(user_id))
        return False

    def __launch_blocker(self, user_id):
        x11_display = self.__get_user_session_display(user_id)
        
        if x11_display != None :
            self.block_status.append(user_id)
            print "[LinuxSessionFiltering] blocking user %s" % user_id
            user_name = self.quarterback.usersmanager.get_username_by_uid(user_id)
            reactor.callInThread(self.__launch_blocker_thread, user_id, user_name, x11_display, self)
        
    def __launch_blocker_thread(self, user_id, user_name, x11_display, linuxsb):
        try:
            proclist = gtop.proclist(gtop.PROCLIST_KERN_PROC_UID, int(user_id))
            env_lang_var = 'C'

            if len(proclist) > 0 :
                for proc in proclist :
                    lang_var = Popen('cat /proc/%s/environ | tr "\\000" "\\n" | grep ^LANG= ' % proc , 
                                     shell=True, stdout=PIPE).stdout.readline().strip("\n")
                    if len(lang_var) > 0 :
                        env_lang_var = lang_var.replace("LANG=","")
                        break
            cmd = ['su', user_name, '-c', 
                   'LANG=%s DISPLAY=%s %s &>> /var/tmp/desktop-blocker-%s.log' % (env_lang_var, x11_display, self.sb, user_id)]
                   
            print cmd

            # hack to start after unity panel has actually been loaded
            # see https://bugs.launchpad.net/nanny/+bug/916788
            #
            # BOH
            env_session_type = None
            if len(proclist) > 0 :
                for proc in proclist :
                    session_type = Popen('cat /proc/%s/environ | tr "\\000" "\\n" | grep ^DESKTOP_SESSION= ' % proc , 
                                     shell=True, stdout=PIPE).stdout.readline().strip("\n")
                    if len(session_type) > 0 :
                        env_session_type = session_type.replace("DESKTOP_SESSION=","")
                        break
            
            if env_session_type == "ubuntu":
                SLEEP_INTERVAL = 2
                intervals_to_wait = 22
                while os.system("pgrep -fl unity-panel-service | grep -v pgrep") != 0 and intervals_to_wait > 0: 
                    intervals_to_wait = intervals_to_wait - 1
                    print "Waiting for the desktop to start", intervals_to_wait
                    time.sleep(SLEEP_INTERVAL)

            time.sleep(SLEEP_INTERVAL)
            # EOH
            
            p = Popen(cmd)
            print "[LinuxSessionFiltering] launching blocker (pid : %s)" % p.pid

            while p.poll() == None :
                time.sleep(1)
                b = threads.blockingCallFromThread(reactor, linuxsb.is_user_blocked, user_id)
                if b == False:
                    p.terminate()
                    print "[LinuxSessionFiltering] Unblocking session %s" % user_id
                    return

            print "[LinuxSessionFiltering] blocker terminated by user interaction"
            threads.blockingCallFromThread(reactor, linuxsb.blocker_terminate_from_thread, user_id, p.poll())
        except:
            print "[LinuxSessionFiltering] blocker terminated by exception"
            threads.blockingCallFromThread(reactor, linuxsb.blocker_terminate_from_thread, user_id, 1)

    def __get_user_session_display(self, user_id):
        d = dbus.SystemBus()
        manager = dbus.Interface(d.get_object("org.freedesktop.ConsoleKit", 
                                              "/org/freedesktop/ConsoleKit/Manager"), 
                                 "org.freedesktop.ConsoleKit.Manager")

        sessions = manager.GetSessionsForUnixUser(int(user_id))
        for session_name in sessions :
            session = dbus.Interface(d.get_object("org.freedesktop.ConsoleKit", session_name),
                                     "org.freedesktop.ConsoleKit.Session")
            x11_display = session.GetX11Display()
            if x11_display != "":
                return x11_display
        
        return None

class LinuxSessionFiltering(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

        self.updater_session_hd = None

    def start(self):
        print "Start Linux Session Filtering"
        self.linuxsb = LinuxSessionBlocker(self.quarterback)
        if self.linuxsb.sb != None :
            print "[LinuxSessionFiltering] start watcher :)"
            self.updater_session_hd = gobject.timeout_add(1000, self.__update_session_blocker_status)

    def stop(self):
        print "Stop Linux Session Filtering"
        if self.updater_session_hd != None:
            gobject.source_remove(self.updater_session_hd)
        
        self.linuxsb.block_status = []
        reactor.iterate(delay=2)
        print "Stopped Linux Session Filtering"


    def __update_session_blocker_status(self):
        blocks = self.quarterback.blocks
        for user_id in blocks.keys() :
            for app_id in blocks[user_id].keys() :
                if app_id != SESSION_APPID :
                    continue

                if self.quarterback.get_available_time(user_id, app_id) == 0 :
                    self.linuxsb.set_block(int(user_id), True)
                    continue

                try:
                    block_status, next_block = self.quarterback.is_blocked(user_id, app_id)
                except:
                    print "[LinuxSessionFiltering] Fail getting self.quarterback.is_blocked"
                    block_status = False

                if block_status == True :
                    self.linuxsb.set_block(int(user_id), True)
                else:
                    self.linuxsb.set_block(int(user_id), False)

        return True
