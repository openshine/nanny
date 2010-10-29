#!/usr/bin/env python

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

import os
import sys
if os.name == "posix":
    import dbus
elif os.name == "nt" :
    from ctypes import *


import gtk
import gtk.gdk
import cairo
import pango
import gobject

import nanny.client.common
import nanny.client.gnome.admin
import time


class DesktopBlocker(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)
        self.set_property("skip-taskbar-hint", True)
        self.set_property("skip-pager-hint", True)
        self.set_property("focus-on-map", True)
        self.set_keep_above(True)
        self.fullscreen()
        self.set_modal(True)

        self.bg_pixbuf = None
        
        screen = gtk.gdk.screen_get_default()
        x0,y0,x1,y1 = screen.get_monitor_geometry(0)
        
        self.set_default_size(screen.get_width(), screen.get_height())
        self.set_decorated(False)
        self.set_app_paintable(True)


        nanny.client.common.Utils.ui_magic (self,
                                            ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nanny_desktop_blocker.ui"),
                                            prefix = "db")
        self.main_vbox.unparent()
        self.add(self.main_vbox)
        self.main_vbox.show_all()

        self.__setup_background()
        self.stick()

        #Signals 
        self.close_button.connect("clicked", self.__close_button_clicked_cb, None)
        self.time_button.connect("clicked", self.__time_button_clicked_cb, None)

    
    def __setup_background(self):
        screen = self.get_screen()
        colormap = screen.get_rgba_colormap()
        
        if colormap != None and screen.is_composited() :
            self.set_colormap(colormap)
            self.__is_composited = True
        else:
            self.__is_composited = False

        self.connect("expose-event", self.__window_expose_event_cb)
    
    def __window_expose_event_cb(self, widget, event):
        context = self.window.cairo_create()

        if self.__is_composited :
            context.set_operator(cairo.OPERATOR_SOURCE)
            context.set_source_rgba(0.2, 0.2, 0.2, 0.8)
            context.paint()
        else:
            context.set_source_rgb(0.2, 0.2, 0.2)
            context.paint()

        return False
        
    def __close_button_clicked_cb(self, widget, data):
        if os.name == "nt" :
            windll.user32.ExitWindowsEx(0)
        sys.exit(0)
        
    def __time_button_clicked_cb(self, widget, data):
        gtk.gdk.keyboard_ungrab()
        self.hide()
        gobject.timeout_add(1000*60*5, self.__timeout_cb)

    def __timeout_cb(self):
        self.show()
        self.time_button.hide()
        self.info_label.hide()
        gtk.gdk.keyboard_grab(self.window)
        return False

        
