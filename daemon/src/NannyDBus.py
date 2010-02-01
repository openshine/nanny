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

import gobject
import os
import dbus
import dbus.service
import dbus.mainloop.glib

class NannyDBus(dbus.service.Object):
    def __init__ (self, quarterback):
        
        self.quarterback = quarterback
        
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        dbus.service.Object.__init__(self,
                                     dbus.service.BusName("org.gnome.Nanny", dbus.SystemBus()),
                                     "/org/gnome/Nanny")

        self.quarterback.connect('block-status', self.__UserNotification_cb)
        self.quarterback.connect('update-users-info', self.__UpdateUsersInfo_cb)

    # org.gnome.Nanny
    # --------------------------------------------------------------
    
    @dbus.service.method("org.gnome.Nanny",
                         in_signature='', out_signature='a(sss)')
    def ListUsers(self):
        return self.quarterback.usersmanager.get_users()

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sia{sa(ss)}', out_signature='b')
    def SetBlocks(self, user_id, app_id, blocks):
        self.quarterback.set_blocks(str(user_id), int(app_id), blocks)
        return True


    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='a{sa(ss)}')
    def GetBlocks(self, user_id, app_id) :
        ret = self.quarterback.get_blocks(user_id, app_id)
        return ret

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='bs', out_signature='')
    def SetActiveWCF(self, active, uid):
        self.quarterback.set_wcf(bool(active), str(uid))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='', out_signature='as')
    def ListWCF(self):
        return self.quarterback.list_wcf_uids()

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sii', out_signature='')
    def SetMaxUseTime(self, user_id, app_id, mins):
        self.quarterback.set_max_use_time(str(user_id), int(app_id), int(mins))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='i')
    def GetMaxUseTime(self, user_id, app_id):
        return self.quarterback.get_max_use_time(user_id, app_id)

    @dbus.service.signal("org.gnome.Nanny",
                         signature='')
    def UpdateUsersInfo(self):
        pass

    def __UpdateUsersInfo_cb(self, quarterback):
        self.UpdateUsersInfo()

    # org.gnome.Nanny.Notification
    # --------------------------------------------------------------

    @dbus.service.signal("org.gnome.Nanny.Notification",
                         signature='bsiii')
    def UserNotification(self, block_status, user_id, app_id, next_change, available_time):
        pass

    def __UserNotification_cb(self, quarterback, block_status, user_id, app_id, next_change, available_time):
        self.UserNotification(block_status, user_id, app_id, next_change, available_time)


    # org.gnome.Nanny.WebDatabase
    # --------------------------------------------------------------

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='sbsss', out_signature='b')
    def AddCustomFilter(self, uid, is_black, name, description, regex):
        return self.quarterback.filter_manager.add_custom_filter(str(uid), bool(is_black), unicode(name),
                                                                          unicode(description), unicode(regex))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='s', out_signature='a(isssb)')
    def ListCustomFilters(self, uid):
        return self.quarterback.filter_manager.list_custom_filters(int(uid))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='i', out_signature='b')
    def RemoveCustomFilter(self, list_id):
        return self.quarterback.filter_manager.remove_custom_filter(int(list_id))

    
    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='isss', out_signature='b')
    def UpdateCustomFilter(self, list_id, name, description, regex):
        return self.quarterback.filter_manager.update_custom_filter(int(list_id),
                                                                    unicode(name),
                                                                    unicode(description),
                                                                    unicode(regex))
    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='', out_signature='as')
    def ListPkgFilters(self):
        return self.quarterback.filter_manager.list_pkg_filter()

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='ss', out_signature='ssasas')
    def GetPkgFilterUserCategories(self, pkg_id, uid):
        return self.quarterback.filter_manager.get_pkg_filter_user_categories(unicode(pkg_id),
                                                                              str(uid)
                                                                              )

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='ssas', out_signature='b')
    def SetPkgFilterUserCategories(self, pkg_id, uid, list_categories):
        list_c = []
        for x in list_categories :
            list_c.append(unicode(x))
            
        return self.quarterback.filter_manager.set_pkg_filter_user_categories(unicode(pkg_id),
                                                                              str(uid),
                                                                              list_c)
                                                                              
    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='ssss', out_signature='b')
    def AddDansGuardianList(self, uid, name, description, list_url):
        return self.quarterback.webcontent_filter.webdb.add_dans_guardian_list(str(uid),
                                                                               unicode(name),
                                                                               unicode(description),
                                                                               unicode(list_url))
