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
import pynotify
import gobject

import nanny.client.common
import nanny.client.gnome.systray

class SystrayNanny(gtk.StatusIcon):
    def __init__(self):
        #atributes
        self.times_left = { 0:[-1, False], 1:[-1, False], 2:[-1, False] , 3:[-1, False] }#cuanto falta
        self.times_show = { 0:-1, 1:-1, 2:-1, 3:-1 }#cuanto quedaba cuando se mostro
        self.app_names = { 0: _("Session"),
                           1: _("Web browser"),
                           2: _("e-Mail"),
                           3: _("Instant messanger")
                         }
        self.look_times = [ 60, 30, 15, 5, 4, 3, 2, 1 ]
        
        #systray
        gtk.StatusIcon.__init__ (self)
        icon_path = os.path.join (nanny.client.gnome.systray.icons_files_dir, "24x24/apps", "nanny.png")
        self.set_from_file(icon_path)
        self.set_visible(True)
        self.set_tooltip("")

        #dbus
        self.dbus = nanny.client.common.DBusClient()
        self.dbus.connect("user-notification", self.__handlerUserNotification)
        
        #timer
        gobject.timeout_add(3000, self.__handlerTimer )

    def __handlerUserNotification(self, dbus, block_status, user_id, app_id, next_change, available_time):
        uid= str(os.getuid())
        if uid==user_id:
            self.times_left[app_id] = [next_change, block_status]

    def __handlerTimer(self):
        mssg=""
        mssg_ready=False
        for app_id in self.times_left:
            if self.times_left[app_id][0]!=-1:
                if self.times_show[app_id] == -1:
                    self.times_show[app_id] = self.times_left[app_id][0] + 60 

                for time in self.look_times:
                    #first element
                    if time == self.look_times[0]:
                        if self.times_left[app_id][0] >= time and self.times_show[app_id]-self.times_left[app_id][0] >= time:
                            self.times_show[app_id]=self.times_left[app_id][0]
                            mssg_ready=True
                    else:
                        if self.times_left[app_id][0]<= time and self.times_show[app_id]-self.times_left[app_id][0] >= time:
                            self.times_show[app_id]=self.times_left[app_id][0]
                            mssg_ready=True

                time = self.__format_time (self.times_left[app_id][0])
                if len (mssg) > 0:
                    mssg += "\n"
                if self.times_left[app_id][1]:
                    mssg += _("In %s the access to <b>%s</b> will be granted.") % (time, self.app_names[app_id])
                else:
                    mssg += _("In %s the access to <b>%s</b> will be denied.") % (time, self.app_names[app_id])

        if mssg_ready:
            self.__showNotification( mssg )
        self.set_tooltip( mssg )
        return True

    def __format_time (self, minutes):
        h, m = divmod(minutes, 60)
        d, h = divmod (h, 24)

        time = ""
        if d > 0:
            if d == 1:
                time += _("1 day")
            else:
                time += _("%s days") % d
        if h > 0:
            if len(time) > 0:
                time += ", "
            if h == 1:
                time += _("1 hour")
            else:
                time += _("%s hours") % h
        if m > 0:
            if len(time) > 0:
                time += ", "
            if m == 1:
                time += _("1 minute")
            else:
                time += _("%s minutes") % m

        return time

    def __showNotification (self, mssg):
        icon_path = os.path.join (nanny.client.gnome.systray.icons_files_dir, "48x48/apps", "nanny.png")

        pynotify.init ("aa")
        self.notificacion = pynotify.Notification ("Nanny", mssg, icon_path)
        self.notificacion.show()
