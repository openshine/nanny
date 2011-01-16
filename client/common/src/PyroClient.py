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

import os
import sys
import gobject
import time
import gtk

from Singleton import *

NANNY_URI="PYROLOC://localhost:7766/org.gnome.Nanny"
NANNY_WCF="PYROLOC://localhost:7766/org.gnome.Nanny.WebDatabase"
NANNY_NOTIFICATION_URI="PYROLOC://localhost:7766/org.gnome.Nanny.Notification"


class PyroClient(gobject.GObject):
    __metaclass__ = Singleton

    __gsignals__ = {'user-notification': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                          (gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_INT))
                   }

    def __init__(self):
        gobject.GObject.__init__(self)
        
        if self.__init_bus() == False:
            raise Exception ('Pyro not initialized')

    def __init_bus(self):
        try:
            import Pyro.core
            
            self.nanny_admin = Pyro.core.getProxyForURI(NANNY_URI)
            self.nanny_wcf = Pyro.core.getProxyForURI(NANNY_WCF)
            self.nanny_notification = Pyro.core.getProxyForURI(NANNY_NOTIFICATION_URI)

            #self.nanny_notification.connect_to_signal ('UserNotification', self.__on_user_notification_cb)

            return True
        except:
            return False

    def is_unlocked(self):
	return True 
        return self.nanny_admin.IsUnLocked()

    def unlock (self):
        return self.nanny_admin.UnLock()

    def list_users(self):
        return self.nanny_admin.ListUsers ()

    def get_blocks (self, user_id, app_id):
        return self.nanny_admin.GetBlocks (user_id, app_id)

    def set_blocks (self, user_id, app_id, blocks):
        return self.nanny_admin.SetBlocks (user_id, app_id, blocks)

    def get_max_use_time (self, user_id, app_id):
        return self.nanny_admin.GetMaxUseTime (user_id, app_id)

    def set_max_use_time (self, user_id, app_id, minutes):
        return self.nanny_admin.SetMaxUseTime (user_id, app_id, int(minutes))

    def set_active_WCF (self, user_id, active):
        return self.nanny_admin.SetActiveWCF (active, user_id)

    def list_WCF (self):
        return self.nanny_admin.ListWCF ()

    def list_custom_filters (self, uid):
        return self.nanny_wcf.ListCustomFilters (uid)

    def add_custom_filter (self, user_id, color, name, description, url):
        print name
        return self.nanny_wcf.AddCustomFilter (user_id, color, name, description, url)

    def update_custom_filter (self, filter_id, name, description, url):
        return self.nanny_wcf.UpdateCustomFilter (filter_id, name, description, url)

    def remove_custom_filter (self, filter_id, reply_handler, error_handler):
	try:
            ret = self.nanny_wcf.RemoveCustomFilter (filter_id)
	    reply_handler(True)
            return ret
        except:
	    error_handler(None)

    def add_pkg_filter (self, name):
        return self.nanny_wcf.AddPkgFilter(name)

    def remove_pkg_filter (self, pkg_id):
        return self.nanny_wcf.RemovePkgFilter(pkg_id)
    
    def update_pkg_filter (self, pkg_id):
        return self.nanny_wcf.UpdatePkgFilter(pkg_id)
    
    def list_pkg_filters (self):
        return self.nanny_wcf.ListPkgFilters()
    
    def get_pkg_filter_metadata (self, pkg_id):
        return self.nanny_wcf.GetPkgFilterMetadata(pkg_id)

    def set_pkg_filter_metadata (self, pkg_id, name, description):
        return self.nanny_wcf.SetPkgFilterMetadata(pkg_id, name, description)
    
    def get_pkg_filter_user_categories (self, pkg_id, uid):
        return self.nanny_wcf.GetPkgFilterUserCategories(pkg_id, uid)

    def set_pkg_filter_user_categories (self, pkg_id, uid, list_categories):
        return self.nanny_wcf.SetPkgFilterUserCategories(pkg_id, uid, list_categories)

    def add_dansguardian_list (self, uid, name, description, list_url, reply_handler, error_handler):
        self.nanny_wcf.AddDansGuardianList (uid, name, description, list_url, reply_handler=reply_handler, error_handler=error_handler, timeout=2000000)

    def check_web_access (self, uid, url):
        return self.nanny_wcf.CheckWebAccess (uid, url)

    def __on_user_notification_cb (self, block_status, user_id, app_id, next_change, available_time):
        self.emit ('user-notification', block_status, user_id, app_id, next_change, available_time)
