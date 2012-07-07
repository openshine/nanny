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
import os.path

import gtk
if os.name == "posix" :
    import pynotify
elif os.name == "nt":
    import nanny.daemon.Win32UsersManager
    import getpass
    from gtkPopupNotify import NotificationStack

import gobject
from gettext import ngettext

from datetime import datetime, timedelta

import nanny.client.common
import nanny.client.gnome.systray
import gettext

ngettext = gettext.ngettext


class SystrayNanny(gtk.StatusIcon):
    def __init__(self):
        #attributes
        self.times_left = { 0:[-1, False, False], 1:[-1, False, False], 2:[-1, False, False] , 3:[-1, False, False] }
        self.app_names = { 0: _("your session"),
                           1: _("web browser"),
                           2: _("e-mail"),
                           3: _("instant messenger")
                         }
        self.notified = {0: -1, 1: -1, 2: -1, 3: -1 }
        self.notify_moments_deny = [ 60, 30, 15, 5, 2, 1, 0 ]
        self.notify_moments_grant = [ 60, 30, 15, 5, 0 ]
        
        #systray
        gtk.StatusIcon.__init__ (self)
        icon_path = os.path.join (nanny.client.gnome.systray.icons_files_dir, "24x24/apps", "nanny.png")
        self.set_from_file(icon_path)
        self.set_visible(False)
        self.set_tooltip("")
        self.last_tooltip = ''

        #dbus
        self.dbus = nanny.client.common.DBusClient()
        
        if os.name == "nt":
            users_manager = nanny.daemon.Win32UsersManager.Win32UsersManager()
            self.uid = ''
            for uid, username, desc in users_manager.get_users() :
                if username == getpass.getuser() :
                    self.uid = uid
                    break
            gobject.timeout_add(1000, self.__block_status_windows_polling)
            self.win_notify = NotificationStack()

        elif os.name == "posix":
            self.dbus.connect("user-notification", self.__handlerUserNotification)

        #timer
        gobject.timeout_add(3000, self.__handlerTimer )

    def __block_status_windows_polling(self):
        ret = self.dbus.get_block_status_by_uid(self.uid)
        for k in ret.keys():
            block_status = ret[k][0]
            user_id = self.uid
            app_id = k
            next_change = ret[k][1]
            available_time = ret[k][2]
            self.__handlerUserNotification(self.dbus,  block_status, 
                                           user_id, app_id, 
                                           next_change, available_time, active)
        
        return True

    def __handlerUserNotification(self, dbus, block_status, user_id, app_id, next_change, available_time, active):
        if os.name == "posix" :
            uid= str(os.getuid())
        elif os.name == "nt":
            uid = self.uid

        if uid==user_id:
            print user_id, app_id, next_change, block_status, available_time, active

            # a bit messy right now
            # this should probably be a special function in QuarterBack
            # is_blocked now deals only with scheduled blocks
            minutes_till_midnight = int(((datetime.now()+timedelta(days=1)).replace(minute=0, hour=0, second=0, microsecond=0) - datetime.now()).seconds/60)
            if (datetime.now() + timedelta(minutes=available_time)).day != datetime.now().day:
                available_time = minutes_till_midnight + self.dbus.get_max_use_time(user_id, app_id)
            elif available_time == 0:
                if (next_change == -1 or (next_change > minutes_till_midnight and block_status == True)):
                    next_change = minutes_till_midnight
                    block_status = True
            
            if next_change != -1 or available_time != -1:
                if next_change != -1 and available_time != -1:
                    if (available_time == 0 and next_change > 0) or next_change <= available_time:
                        next_ch_unified = next_change
                    else:
                        next_ch_unified = available_time
                        block_status = False
                else:
                    if next_change == -1:
                        next_ch_unified = available_time
                        block_status = False
                    elif available_time == -1:
                        next_ch_unified = next_change
            else:
                next_ch_unified = -1

            self.times_left[app_id] = [next_ch_unified, block_status, active]


    def __handlerTimer(self):
        msg = ""
        need_to_notify = False
        
        for app_id in self.times_left:
            next_change = self.times_left[app_id][0]
            block_status = self.times_left[app_id][1]
            active = self.times_left[app_id][2]
            if self.times_left[app_id][0] != -1:
            
                active_notify = -1
                if block_status == True:
                    moments_list = self.notify_moments_grant
                else:
                    moments_list = self.notify_moments_deny
                    
                for moment in moments_list:
                    if next_change - 1 <= moment:
                        active_notify = moment
                        continue
                    else:
                        break

                if ((active and not block_status) or block_status) and next_change > 1:
                    # running and will be blocked or will be released and ...
                    # (not running and will be blocked is of no interest)

                    time = self.__format_time (next_change - 1) # -1 is to overcome lags
                    if len(msg) > 0:
                        msg += "\n"
                    if block_status == True:
                        if next_change <= 1:
                            msg += _("The access to %(app)s granted.") % {'app': self.app_names[app_id]}
                        else:
                            # To translators: In x-minutes the access to <app> will be granted
                            msg += _("In %(time)s the access to %(app)s will be granted.") % {'time': time, 'app': self.app_names[app_id]}
                    else:
                        if next_change <= 1:
                            msg += _("The access to %(app)s denied.") % {'app': self.app_names[app_id]}
                        else:
                            # To translators: In x-minutes the access to <app> will be denied
                            msg += _("In %(time)s the access to %(app)s will be denied.") % {'time': time, 'app': self.app_names[app_id]}

                    if self.notified[app_id] != active_notify:
                        self.notified[app_id] = active_notify
                        need_to_notify = True
                        
        if need_to_notify:
            print "NOTIFY:", msg
            self.__showNotification(msg)
        
        if self.last_tooltip != msg : 
            self.set_tooltip(msg)
            self.last_tooltip = msg
            print "TOOLTIP:", msg
        
        if len(msg) != 0 :
            self.set_visible(True)
        else:
            self.set_visible(False)

        return True

    def __format_time (self, minutes):
        h, m = divmod(minutes, 60)
        d, h = divmod (h, 24)

        time_list = []
        if d > 0:
            time_list.append(ngettext("%d day", "%d days", d) % d)
        if h > 0:
            time_list.append(ngettext("%d hour", "%d hours", h) % h)
        if m > 0:
            time_list.append(ngettext("%d minute", "%d minutes", m) % m)
        # Translators: This is the separator between time strings, like '1 day, 2 hours, 3 minutes'
        time = _(", ").join(time_list)

        return time

    def __showNotification (self, msg):
        icon_path = os.path.join (nanny.client.gnome.systray.icons_files_dir, "48x48/apps", "nanny.png")

        if os.name == "posix":
            pynotify.init ("aa")
            self.notificacion = pynotify.Notification ("Nanny", msg, icon_path)
            self.notificacion.show()
        elif os.name == "nt":
            self.win_notify.new_popup("Nanny", msg, icon_path)
