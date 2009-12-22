#!/usr/bin/env python

# Copyright (C) 2009 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
#   Cesar Garcia Tapia <cesar.garcia.tapia at openshine.com>
#   Luis de Bethencourt <luibg at openshine.com>
#   Pablo Vieytes <pvieytes at openshine.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import os
import sys
import gobject
import time
import dbus
import dbus.glib
import gtk

from Singleton import *

NANNY_PATH="/org/gnome/Nanny"
NANNY_URI="org.gnome.Nanny"
NANNY_WCF="org.gnome.Nanny.WebDatabase"
NANNY_NOTIFICATION_URI="org.gnome.Nanny.Notification"


class DBusClient(gobject.GObject):
    __metaclass__ = Singleton

    __gsignals__ = {'user-notification': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                          (gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_INT))
                   }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.dbus = None

        if self.__init_bus() == False:
            raise Exception ('DBus not initialized')

    # Decorators (nanny_dbus_crash)
    def nanny_dbus_crash():
        def wrap (f):
            def _f(self, *args, **kw):
                try:
                    return f(self, *args, **kw)
                except:
                    self.dbus = None
                    if self.__init_bus() == False:
                        self.__nanny_dbus_crash_info_dialog()
                    else:
                        try:
                            return f(self, *args, **kw)
                        except:
                            self.__nanny_dbus_crash_info_dialog()
            return _f
        return wrap

    def __nanny_dbus_crash_info_dialog(self):
        msg = gtk.MessageDialog(parent=None, flags=0,
                                type=gtk.MESSAGE_ERROR,
                                buttons=gtk.BUTTONS_CLOSE, message_format=None)
        msg.set_markup(_(u"<b>NannyDaemon unavailable</b>"))
        msg.format_secondary_markup(_(u"NannyDaemon is not activated or does not work properly.\nPlease try to reactivate it."))
        ret = msg.run()
        msg.destroy()

        sys.exit(0)

    def __init_bus(self):
        try:
            self.dbus = dbus.SystemBus()

            self.nanny_obj = self.dbus.get_object (NANNY_URI,
                                                   NANNY_PATH)
            self.nanny_admin = dbus.Interface(self.nanny_obj,
                                              NANNY_URI)
            self.nanny_wcf = dbus.Interface(self.nanny_obj,
                                              NANNY_WCF)

            self.nanny_notification = dbus.Interface(self.nanny_obj,
                                              NANNY_NOTIFICATION_URI)

            self.nanny_notification.connect_to_signal ('UserNotification', self.__on_user_notification_cb)

            return True
        except:
            return False

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

    def add_custom_filter (self, user_id, color, name, description, url):
        return self.nanny_wcf.AddCustomFilter (user_id, color, name, description, url)

    def add_dansguardian_list (self, uid, name, description, list_url, reply_handler, error_handler):
        self.nanny_wcf.AddDansGuardianList (uid, name, description, list_url, reply_handler=reply_handler, error_handler=error_handler, timeout=2000000)

    def check_web_access (self, uid, url):
        return self.nanny_wcf.CheckWebAccess (uid, url)

    def list_filters (self, uid):
        return self.nanny_wcf.ListFilters (uid)

    def remove_filter (self, filter_id, reply_handler, error_handler):
        return self.nanny_wcf.RemoveFilter (filter_id, reply_handler=reply_handler, error_handler=error_handler, timeout=2000000)

    def __on_user_notification_cb (self, block_status, user_id, app_id, next_change, available_time):
        self.emit ('user-notification', block_status, user_id, app_id, next_change, available_time)
