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
import sys

from twisted.internet import reactor
from twisted.application import internet, service
from twisted.web import server
from twisted.enterprise import adbapi

from nanny.daemon.proxy.TwistedProxy import ReverseProxyResource as ProxyService
from nanny.daemon.proxy.Controllers import WebDatabase
from nanny.daemon.Win32SessionFiltering import WinPopenAsUser

import _winreg

PORT_START_NUMBER=53000

if not hasattr(sys, "frozen") :
    file_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for x in range(6):
        file_dir = os.path.dirname(file_dir)
    root_path = file_dir
    
    WEBDATABASE = os.path.join(root_path, "var", "lib", "nanny", "webs.db")
else:
    WEBDATABASE = os.path.join(os.environ["ALLUSERSPROFILE"], "Gnome", "nanny", "webs.db")


class Win32WebContentFiltering(gobject.GObject) :
    def __init__(self, quarterback, app) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.app = app
        self.ffb = None

        if not hasattr(sys, "frozen") :
            file_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for x in range(6):
                file_dir = os.path.dirname(file_dir)
            root_path = file_dir
            sbin_dir = os.path.join(root_path, "sbin")
            if os.path.exists(os.path.join(sbin_dir, "nanny-firefox-blocker")) :
                self.ffb = "python %s" % os.path.join(sbin_dir, "nanny-firefox-blocker")
        else:
            sbin_dir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
            if os.path.exists(os.path.join(sbin_dir, "nanny-firefox-blocker.exe")):
                self.ffb = os.path.join(sbin_dir, "nanny-firefox-blocker.exe")

        if self.ffb != None :
            print "[Win32WebContentFiltering] firefox blocker blocker : '%s'" % self.ffb

        database_exists = False
        if os.path.exists(WEBDATABASE) :
            database_exists = True
        
        self.dbpool = adbapi.ConnectionPool('sqlite3', WEBDATABASE, check_same_thread=False)
        self.webdb = WebDatabase(self.dbpool)

        if database_exists == False :
            self.webdb.create()
        
        self.services={}
        
        reactor.addSystemEventTrigger("after", "startup", self.start)
        reactor.addSystemEventTrigger("before", "shutdown", self.stop)

        self.quarterback.connect("add-wcf-to-uid", self.__start_proxy)
        self.quarterback.connect("remove-wcf-to-uid", self.__stop_proxy)

        self.update_proxy_settings_hd = None
        self.update_proxy_settings_firefox_hd = None

        self.proxy_helper = Win32ProxyHelper(self.quarterback.usersmanager)
        
    def start(self):
        print "Start Win32 Web Content Filtering"
        for uid in self.quarterback.wcf_uid_list :
            self.__start_proxy(self.quarterback, uid)

        gobject.timeout_add(5000, self.__launch_proxy_updater)

    def stop(self):
        print "Stop Win32 Web Content Filtering"
        for uid in self.services.keys() :
            self.__stop_proxy(self.quarterback, uid)
        
        if self.update_proxy_settings_hd != None :
            gobject.source_remove(self.update_proxy_settings_hd)
        if self.update_proxy_settings_firefox_hd != None :
            gobject.source_remove(self.update_proxy_settings_firefox_hd)
        
        self.proxy_helper.clean_all_proxy_conf()

    def __start_proxy(self, quarterback, uid):
        if not self.services.has_key(uid) :
            root = ProxyService(uid, quarterback.filter_manager)
            sc = service.IServiceCollection(self.app)
            site = server.Site(root)
            
            for port in range(PORT_START_NUMBER, PORT_START_NUMBER+5000) :
                try:
                    i = internet.TCPServer(port, site)
                    i.setServiceParent(sc)
                except:
                    continue
                
                self.services[uid]=(i, port)
                return
        
    def __stop_proxy(self, quarterback, uid):
        if not self.services.has_key(uid) :
            return True
        else:
            i,port = self.services.pop(uid)
            i.stopService()

    def __launch_proxy_updater(self):
        self.update_proxy_settings_hd = gobject.timeout_add(1000, self.__update_proxy_settings)
        self.update_proxy_settings_firefox_hd = gobject.timeout_add(5000, self.__update_proxy_settings_firefox)

    def __update_proxy_settings_firefox(self):
        session_uid = int(self.quarterback.win32top.get_current_user_session())
        if session_uid != 0 :
            if self.services.has_key(str(session_uid)) :
                user_name = None
                for uid, name, fullname in self.quarterback.usersmanager.get_users() :
                    if uid == str(session_uid) :
                        user_name = name
                        break
                
                if user_name != None :
                    reactor.callInThread(self.__launch_firefox_blocker, self, user_name)
        
        return True

    def __launch_firefox_blocker(self, wcf, user_name):
        import time
        try:
            p = WinPopenAsUser(wcf.ffb + " %s" % user_name)
            while p.poll() == None:
                time.sleep(1)
        except:
            print "[W32WebcontentFiltering] firefox blocker exception"
        
        
    def __update_proxy_settings(self):
        session_uid = int(self.quarterback.win32top.get_current_user_session())
        if session_uid != 0 :
            host = None
            port = None
            proxy_info = None
            
            is_enabled = self.proxy_helper.get_proxy_enable(session_uid)
            proxy_info = self.proxy_helper.get_proxy_http(session_uid)
            if proxy_info != None :
                host = proxy_info[0]
                port = proxy_info[1]

            if self.services.has_key(str(session_uid)) :
                if is_enabled == False:
                    print "[W32WebContentFiltering] Enable proxy (uid = %s, port = %s)" % (session_uid, self.services[str(session_uid)][1])
                    self.proxy_helper.set_proxy_enable(session_uid, True)
                    self.proxy_helper.set_proxy_http(session_uid, "localhost", self.services[str(session_uid)][1])
                    return True
                else:
                    if not ( host == "localhost" and port != None and port == str(self.services[str(session_uid)][1]) ) :
                        print "[W32WebContentFiltering] (BBP) Enable proxy (uid = %s, port = %s)" % (session_uid, self.services[str(session_uid)][1])
                        self.proxy_helper.set_proxy_http(session_uid, "localhost", self.services[str(session_uid)][1])
                        return True
            else:
                if is_enabled == True :
                    if host == "localhost" and port != None :
                        if  PORT_START_NUMBER <=  int(port) < PORT_START_NUMBER + 5000 :
                            print "[W32WebContentFiltering] Disable proxy (uid = %s)" % (session_uid)
                            self.proxy_helper.del_proxy_http(session_uid)
                            return True
        
        #print "[W32WebContentFiltering] Update proxy not necessary : (s:%s, st:%s, h:%s, p:%s)" % (session_uid, is_enabled, host, port)
        return True

class Win32ProxyHelper : 
    def __init__(self, users_manager):
        self.users_manager = users_manager

    def get_proxy_enable(self, uid):
        hkey = self.__get_user_internet_settings_hkey(uid)
        try:
            (val, vtype) = _winreg.QueryValueEx(hkey, "ProxyEnable")
            _winreg.CloseKey(hkey)
            return bool(int(val))
        except:
            print "[W32ProxyHelper] Exception get_proxy_enabled"
            return False

    def set_proxy_enable(self, uid, value):
        hkey = self.__get_user_internet_settings_hkey(uid)
        if value == True : 
            #_winreg.SetValueEx (hkey, "ProxyEnable", 0, _winreg.REG_DWORD, 1)
            self.__set_proxy_enable_winreg(uid, 1)
        else:
            #_winreg.SetValueEx (hkey, "ProxyEnable", 0, _winreg.REG_DWORD, 0)
            self.__set_proxy_enable_winreg(uid, 0)
            
        _winreg.CloseKey(hkey)
        print "[W32ProxyHelper] set proxy enable status (uid:%s) -> %s" % (uid, value)


    def get_proxy_http(self, uid):
        hkey = self.__get_user_internet_settings_hkey(uid)
        try:
            (val, vtype) = _winreg.QueryValueEx(hkey, "ProxyServer")
            proxy_servers = str(val)

            if proxy_servers == '' :
                return None
            else:
                for proxy_t in proxy_servers.split(";"):
                    if proxy_t.startswith("http=") :
                        return proxy_t[5:].split(":")
            return None
        except:
            return None

    def set_proxy_http(self, uid, host, port):
        hkey = self.__get_user_internet_settings_hkey(uid)
        try:
            proxy_servers = ''
            try:
                (val, vtype) = _winreg.QueryValueEx(hkey, "ProxyServer")
                proxy_servers = str(val)
            except:
                pass

            new_proxy_list = ''

            previous_http_proxy = False

            for proxy_t in proxy_servers.split(";"):
                p_tmp = ''
                if len(proxy_t) < 3 :
                    continue

                if proxy_t.startswith("http=") :
                    previous_http_proxy = True
                    p_tmp = "http=%s:%s" % (host, port)
                else:
                    p_tmp = proxy_t
                new_proxy_list = new_proxy_list + p_tmp + ";"

            if new_proxy_list == '' :
                new_proxy_list = "http=%s:%s" % (host, port)
            else:
                if previous_http_proxy == False:
                    http_proxy = "http=%s:%s;" % (host, port)
                    new_proxy_list = http_proxy + new_proxy_list[:-1]
                else:
                    new_proxy_list = new_proxy_list[:-1]

            print "[W32ProxyHelper] set proxy info (uid:%s) -> '%s'" % (uid, new_proxy_list)
            #_winreg.SetValueEx (hkey, "ProxyServer", 0, _winreg.REG_SZ, new_proxy_list)
            self.__set_proxy_conf_winreg(uid, new_proxy_list)
            _winreg.CloseKey(hkey)
        except:
            print "[W32ProxyHelper] Exception set_proxy_http"

    def del_proxy_http(self, uid):
        hkey = self.__get_user_internet_settings_hkey(uid)
        try:
            proxy_servers = ''
            try:
                (val, vtype) = _winreg.QueryValueEx(hkey, "ProxyServer")
                proxy_servers = str(val)
            except:
                pass

            new_proxy_list = ''
            for proxy_t in proxy_servers.split(";"):
                p_tmp = ''
                if len(proxy_t) < 3 :
                    continue

                if proxy_t.startswith("http=") :
                    continue
                else:
                    p_tmp = proxy_t
                new_proxy_list = new_proxy_list + p_tmp + ";"

            if new_proxy_list != '' :
                new_proxy_list = new_proxy_list[:-1]
            else:
                self.set_proxy_enable(uid, False)

            print "[W32ProxyHelper] del http proxy (uid:%s) -> '%s'" % (uid, new_proxy_list)
            #_winreg.SetValueEx (hkey, "ProxyServer", 0, _winreg.REG_SZ, new_proxy_list)
            self.__set_proxy_conf_winreg(uid, new_proxy_list)
            _winreg.CloseKey(hkey)
        except:
            print "[W32ProxyHelper] Exception set_proxy_http"

    def clean_all_proxy_conf(self):
        users_list = self.users_manager.get_users()

        for uid, name, full_name in users_list :
            hkey = self.__get_user_internet_settings_hkey(int(uid))
            if hkey != None :
                host = None
                port = None
                proxy_info = None
            
                is_enabled = self.get_proxy_enable(int(uid))
                proxy_info = self.get_proxy_http(int(uid))
                if proxy_info != None :
                    host = proxy_info[0]
                    port = proxy_info[1]

                if is_enabled == True :
                    if host == "localhost" and port != None :
                        if  PORT_START_NUMBER <=  int(port) < PORT_START_NUMBER + 5000 :
                            print "[W32WProxyHelper] Disable proxy (uid = %s)" % (int(uid))
                            self.del_proxy_http(int(uid))

                _winreg.CloseKey(hkey)
            else:
                user_sid = self.users_manager.get_sid_from_uid(uid)
                if user_sid == None :
                    print "[W32ProxyHelper] USER SID = None"
                    continue

                proxy_path = r"%s\Software\Microsoft\Windows\CurrentVersion\Internet Settings" % user_sid
                
                if os.path.exists(os.path.join(os.environ["SYSTEMDRIVE"], "\\Documents and Settings", name, "NTUSER.DAT")) :
                    hiv_path = os.path.join(os.environ["SYSTEMDRIVE"], "\\Documents and Settings", name, "NTUSER.dat")
                elif os.path.exists(os.path.join(os.environ["SYSTEMDRIVE"], "\\Users", name, "NTUSER.DAT")) :
                    hiv_path = os.path.join(os.environ["SYSTEMDRIVE"], "\\Users", name, "NTUSER.DAT")
                else:
                    print "[W32ProxyHelper] Fail finding NTUSERS.dat of %s" % uid
                    continue 

                print 'reg load "HKU\\%s" "%s"' % (user_sid , hiv_path)
                os.system('reg load "HKU\\%s" "%s"' % (user_sid , hiv_path))
                host = None
                port = None
                proxy_info = None
            
                is_enabled = self.get_proxy_enable(int(uid))
                print "proxy enabled = %s (uid: %s)" % (is_enabled, uid)
                proxy_info = self.get_proxy_http(int(uid))
                print "proxy info = %s (uid: %s)" % (proxy_info, uid)
                if proxy_info != None :
                    host = proxy_info[0]
                    port = proxy_info[1]

                if is_enabled == True :
                    if host == "localhost" and port != None :
                        if  PORT_START_NUMBER <=  int(port) < PORT_START_NUMBER + 5000 :
                            print "[W32WProxyHelper] Disable proxy (uid = %s)" % (int(uid))
                            self.del_proxy_http(int(uid))
                
                print 'reg unload "HKU\\%s"' % (user_sid)
                os.system('reg unload "HKU\\%s"' % (user_sid))
    
    def __get_user_internet_settings_hkey(self, uid):
        try:
            root = _winreg.HKEY_USERS
            user_sid = self.users_manager.get_sid_from_uid(uid)
            if user_sid == None :
                print "[W32ProxyHelper] USER SID = None"
                return

            proxy_path = r"%s\Software\Microsoft\Windows\CurrentVersion\Internet Settings" % user_sid
            hkey = _winreg.OpenKey (root, proxy_path)
            return hkey
        except:
            return None

    def __set_proxy_enable_winreg(self, uid, value):
        user_sid = self.users_manager.get_sid_from_uid(uid)
        if user_sid == None :
            print "[W32ProxyHelper] USER SID = None"
            return
        
        proxy_path = r"%s\Software\Microsoft\Windows\CurrentVersion\Internet Settings" % user_sid
        ret = os.system('reg add "HKU\\%s" /v ProxyEnable /t REG_DWORD /d %s /f > NUL' % (proxy_path, int(value)))
        if ret != 0 :
            print "[W32ProxyHelper] __set_proxy_enable_winreg"

    def __set_proxy_conf_winreg(self, uid, value):
        user_sid = self.users_manager.get_sid_from_uid(uid)
        if user_sid == None :
            print "[W32ProxyHelper] USER SID = None"
            return
        
        proxy_path = r"%s\Software\Microsoft\Windows\CurrentVersion\Internet Settings" % user_sid
        ret = os.system('reg add "HKU\\%s" /v ProxyServer /t REG_SZ /d "%s" /f > NUL' % (proxy_path, value))
        if ret != 0 :
            print "[W32ProxyHelper] __set_proxy_conf_winreg"
