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
import sys

from twisted.internet import reactor, threads
from time import localtime, strftime

(
SESSION_APPID,
WEB_APPID,
MAIL_APPID,
IM_APPID) = range(4)

class Win32SessionBlocker(gobject.GObject) :
    def __init__(self, quarterback):
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.sb = None
        self.block_status = []

        if not hasattr(sys, "frozen") :
            file_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for x in range(6):
                file_dir = os.path.dirname(file_dir)
            root_path = file_dir
            sbin_dir = os.path.join(root_path, "sbin")
            if os.path.exists(os.path.join(sbin_dir, "nanny-desktop-blocker")) :
                self.sb = "python %s" % os.path.join(sbin_dir, "nanny-desktop-blocker")
        else:
            sbin_dir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
            if os.path.exists(os.path.join(sbin_dir, "nanny-desktop-blocker.exe")):
                self.sb = os.path.join(sbin_dir, "nanny-desktop-blocker.exe")

        if self.sb != None :
            print "[W32SessionFiltering] desktop blocker : '%s'" % self.sb

    def is_user_blocked(self, user_id):
        if user_id in self.block_status:
            return True
        else:
            return False

    def blocker_terminate_from_thread(self, user_id, ret):
        print "[W32SessionFiltering] self.blocker_terminate_from_thread %s %s" % (user_id, ret)
        if ret == 0:
            self.block_status.pop(self.block_status.index(user_id))
            print "[W32SessionFiltering] unblocking user %s" % user_id
            try:
                from ctypes import *
                session_uid = self.quarterback.win32top.get_current_user_session()
                print "s: %s == u: %s ->> %s" % (session_uid, user_id, int(session_uid) == int(user_id))
                if int(session_uid) == int(user_id) :
                    print "[W32SessionFiltering] Quiting session"
                    windll.user32.ExitWindowsEx(0)
            except:
                print "[W32SessionFiltering] Something wrong quiting from session"
        else:
            print "[W32SessionFiltering] User or other try to kill blocker :)"
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

    def __launch_blocker_to_badboy(self, user_id):
        session_uid = self.quarterback.win32top.get_current_user_session()
        if int(session_uid) == int(user_id) :
            reactor.callInThread(self.__launch_blocker_thread, user_id, self)
        else:
            self.block_status.pop(self.block_status.index(user_id))
        return False

    def __launch_blocker(self, user_id):
        self.block_status.append(user_id)
        print "[W32SessionFiltering] blocking user %s" % user_id
        reactor.callInThread(self.__launch_blocker_thread, user_id, self)
        
    def __launch_blocker_thread(self, user_id, win32sb):
        import subprocess
        import time

        p = subprocess.Popen(win32sb.sb, shell=False)
        print "[W32SessionFiltering] launching blocker (pid : %s)" % p.pid
        while p.poll() == None :
            time.sleep(1)
            b = threads.blockingCallFromThread(reactor, win32sb.is_user_blocked, user_id)
            if b == False:
                p.kill()
                print "[W32SessionFiltering] Unblocking session %s" % user_id
                while p.poll() == None :
                    print "[W32SessionFiltering] killing %s" % p.pid
                return

        print "[W32SessionFiltering] blocker terminated by user interaction"
        threads.blockingCallFromThread(reactor, win32sb.blocker_terminate_from_thread, user_id, p.poll())
        

class Win32SessionFiltering(gobject.GObject) :
    def __init__(self, quarterback) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        
        reactor.addSystemEventTrigger("before", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

    def start(self):
        print "Start Win32 Session Filtering"
        self.win32sb = Win32SessionBlocker(self.quarterback)
        if self.win32sb.sb != None :
            print "[W32SessionFiltering] start watcher :)"
            gobject.timeout_add(1000, self.__update_session_blocker_status)

    def stop(self):
        self.win32sb.block_status = []
        print "Stop Win32 Session Filtering"


    def __update_session_blocker_status(self):
        session_uid = str(self.quarterback.win32top.get_current_user_session())
        blocks = self.quarterback.blocks

        for user_id in blocks.keys() :
            if int(user_id) == int(session_uid):
                for app_id in blocks[user_id].keys() :
                    if app_id != SESSION_APPID :
                        continue
                    
                    if self.quarterback.get_available_time(user_id, app_id) == 0 :
                        self.win32sb.set_block(int(user_id), True)
                        continue

                    try:
                        block_status, next_block = self.quarterback.is_blocked(user_id, app_id)
                    except:
                        print "[W32SessionFiltering] Fail getting self.quarterback.is_blocked"
                        block_status = False

                    if block_status == True :
                        self.win32sb.set_block(int(user_id), True)
                    else:
                        self.win32sb.set_block(int(user_id), False)

        return True

                    
