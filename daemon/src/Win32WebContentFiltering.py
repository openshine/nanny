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
from twisted.application import internet, service
from twisted.web import server
from twisted.enterprise import adbapi

from nanny.daemon.proxy.TwistedProxy import ReverseProxyResource as ProxyService
from nanny.daemon.proxy.Controllers import WebDatabase

import _winreg

PORT_START_NUMBER=53000
WEBDATABASE='C:\\WINDOWS\\nanny_data\\webs.db'

class Win32WebContentFiltering(gobject.GObject) :
    def __init__(self, quarterback, app) :
        gobject.GObject.__init__(self)
        self.quarterback = quarterback
        self.app = app

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
        
    def start(self):
        print "Start Win32 Web Content Filtering"
        for uid in self.quarterback.wcf_uid_list :
            self.__start_proxy(self.quarterback, uid)
        
        gobject.timeout_add(5000, self.__launch_proxy_updater)

    def stop(self):
        print "Stop Win32 Web Content Filtering"
        for uid in self.services.keys() :
            self.__stop_proxy(self.quarterback, uid)
        gobject.source_remove(self.update_proxy_settings_hd)
        print "Disabling proxy winreg"
        self.__set_proxy_settings(False)
        self.__show_proxy_settings()

    def __start_proxy(self, quarterback, uid):
        if not self.services.has_key(uid) :
            root = ProxyService(uid, quarterback.filter_manager)
            sc = service.IServiceCollection(self.app)
            site = server.Site(root)
            
            for port in range(PORT_START_NUMBER, PORT_START_NUMBER+5000) :
                try:
                    i = internet.TCPServer(port, site)
                    i.setServiceParent(sc)
                    print "[Win32WebContentFiltering] Starting proxy (uid: %s, port: %s)" % (uid, port)
                except:
                    continue
                
                self.services[uid]=(i, port)
                #self.__add_rule(uid, port)
                return
        
    def __stop_proxy(self, quarterback, uid):
        if not self.services.has_key(uid) :
            return True
        else:
            i,port = self.services.pop(uid)
            i.stopService()
            print "[Win32WebContentFiltering] Stoped proxy (uid: %s, port: %s)" % (uid, port)
            session_uid = int(self.quarterback.win32top.get_current_user_session())
            if str(session_uid) == str(uid):
                print "[Win32WebContentFiltering] Disabling proxy winreg cfg"
                self.__set_proxy_settings(False)
                self.__show_proxy_settings()
            #self.__remove_rule(uid, port)

    def __launch_proxy_updater(self):
        self.update_proxy_settings_hd = gobject.timeout_add(1000, self.__update_proxy_settings)

    def __update_proxy_settings(self):
        session_uid = int(self.quarterback.win32top.get_current_user_session())
        if session_uid == 0:
            is_enabled, http_server = self.__get_proxy_info()
            if is_enabled == 1:
                self.__set_proxy_settings(False)
                self.__show_proxy_settings()
        else:
            if self.services.has_key(str(session_uid)) :
                is_enabled, http_server = self.__get_proxy_info()

                changed = False
                if is_enabled == 0 :
                    self.__set_proxy_settings(True, "localhost:%s" % self.services[str(session_uid)][1])
                    changed = True

                if http_server != "localhost:%s" % self.services[str(session_uid)][1] :
                    self.__set_proxy_settings(True, "localhost:%s" % self.services[str(session_uid)][1])
                    changed = True
            
                if changed == True:
                    print "SomeOne tryed to change the proxy settings, revert to nanny proxy"
                    self.__show_proxy_settings()

        return True

    def __set_proxy_settings(self, enable, http_proxy_server='') :
        root = _winreg.HKEY_CURRENT_USER
        proxy_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

        hKey = _winreg.CreateKey (root, proxy_path)

        if enable == True:
            _winreg.SetValueEx (hKey, "ProxyEnable", 0, _winreg.REG_DWORD, 1)
        else:
            _winreg.SetValueEx (hKey, "ProxyEnable", 0, _winreg.REG_DWORD, 0)

        if http_proxy_server != '' :
            proxy_cfg = ''
            try:
                (val, vtype) = _winreg.QueryValueEx(hKey, "ProxyServer")
                proxy_cfg = str(val)
            except:
                pass

            if proxy_cfg == '':
                _winreg.SetValueEx (hKey, "ProxyServer", 0, _winreg.REG_SZ, "http=%s" % http_proxy_server)
            else:
                proxy_list = proxy_cfg.split(";")
                proxy_list_new = []
                for proxy_t in proxy_list :
                    if proxy_t.startswith("http="):
                        proxy_list_new.append("http=%s" % http_proxy_server)
                    else:
                        proxy_list_new.append(proxy_t)

                proxy_new_string = ''
                if len(proxy_list_new) == 1 :
                    proxy_new_string = proxy_list_new[0]
                else:
                    for proxy_t in proxy_list_new :
                        proxy_new_string = proxy_new_string + proxy_t + ";"
                    proxy_new_string = proxy_new_string[:-1]

                _winreg.SetValueEx (hKey, "ProxyServer", 0, _winreg.REG_SZ, proxy_new_string)

        _winreg.CloseKey(hKey)

    def __get_proxy_info(self):
        root = _winreg.HKEY_CURRENT_USER
        proxy_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        hKey = _winreg.OpenKey (root, proxy_path)
        
        is_enabled = 0
        try:
            (val, vtype) = _winreg.QueryValueEx(hKey, "ProxyEnable")
            is_enabled = int(val)
        except:
            pass

        http_server = ''
        try:
            (val, vtype) = _winreg.QueryValueEx(hKey, "ProxyServer")
            proxy_servers = str(val)
            for proxy_t in proxy_servers.split(";"):
                if proxy_t.startswith("http=") :
                    http_server = proxy_t[5:]
                    break
        except:
            pass
        
        _winreg.CloseKey(hKey)
        return is_enabled, http_server
        
    def __show_proxy_settings(self):
        root = _winreg.HKEY_CURRENT_USER
        proxy_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        hKey = _winreg.OpenKey (root, proxy_path)

        def get_reg_info(name):
            try:
                (val, vtype) = _winreg.QueryValueEx(hKey, name)
                print " >> %s : '%s' (vtype : %s)" % (name, str(val), vtype)
            except:
                print " >> %s : ''" % name

        settings = ["ProxyEnable", "ProxyServer"]
        print "[W32WebContentFiltering] New registry info"
        for s in settings :
            get_reg_info(s)
        print "------------------------------------------"
        _winreg.CloseKey(hKey)
