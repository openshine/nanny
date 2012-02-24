#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009,2010 Junta de Andalucia
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

import gtop

from subprocess import Popen, PIPE

import traceback # for debugging

import nanny.client.common.DBusClient
dbus_client = nanny.client.common.DBusClient ()

class DesktopBlocker(gtk.Window):

    def __init__(self):

        print "***", time.asctime(), "Initializing desktop blocker... ***"

        try:
            self.dbus_client = nanny.client.common.DBusClient ()
        except:
            print "Nanny daemon not found"
        
        self.uid = str(os.getuid())
            
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

        self.__setup_background()
        self.stick()

        self.add(self.main_vbox)
        self.main_vbox.show_all()

        self.__setup_ui()

        self.close_button.connect("clicked", self.__close_button_clicked_cb, None)
        self.time_button.connect("clicked", self.__time_button_clicked_cb, None)
        self.buy_time_button.connect("clicked", self.__buy_time_button_clicked_cb, None)

        self.close_button_text = self.close_button.get_label()

    def __setup_ui(self, mercy_button=True):

        print "Setting up UI"

        no_chores = (not self.dbus_client.is_chore_available(self.uid)) or self.dbus_client.is_blocked(self.uid, 0)[0]

        print "Chores list:", not no_chores

        if no_chores:
        
            for c in self.inventory.get_children():
                self.inventory.remove(c)
        	
            self.inventory.show_all()

            self.buy_time_button.hide()
        
        else:
        
            chores_list = self.dbus_client.list_chores(self.uid, available=True)

            vb = gtk.VBox()
            rb = None

            for line in chores_list:
            
                # it could be nice to use 1:06 style layout instead of 1,1
                # maybe switch to minutes after all
                # time.strftime(_('%H:%M'), time.gmtime(int(line[3])*60))

                rb = gtk.RadioButton(rb, line[6] + _(" (%s min)") % (line[3]))
                rb.set_tooltip_text(line[7])
                rb.connect("toggled", self.__inventory_toggle, [line[0], line[3]])
                rb.set_can_focus(False) # otherwise badboys can hack by pressing enter on selected radiobutton
                l = rb.get_children()[0] # gtk.Label
                l.modify_fg(gtk.STATE_ACTIVE, gtk.gdk.color_parse("white"))
                l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
                vb.add(rb)

            rb = gtk.RadioButton(rb)
            rb.connect("toggled", self.__inventory_toggle)
            vb.add(rb)
      
            self.inv_none_button =  rb
            self.inv_none_button.set_active(True)
                
            hb = gtk.HBox()
            hb.pack_start(vb, expand=True, fill=True, padding=20)

            for c in self.inventory.get_children():
                self.inventory.remove(c)

            self.inventory.add(hb)
            self.inventory.show_all()

            self.buy_time_button.show()

            # to make none of radio buttons selected
            self.inv_none_button.hide()

        print "Mercy button:", mercy_button

        if not mercy_button:
            self.time_button.hide()
            self.info_label.hide()

        delay = 0
        if self.window is not None:
            while gtk.gdk.keyboard_grab (self.window) != gtk.gdk.GRAB_SUCCESS:
                print "Grab delaying..."
                delay += 0.05
                time.sleep (0.05)
            if delay > 0:
                print "... ", delay, "sec"
                
        self.already_closed = False
        self.close_button_countdown = 99
        
        if self.dbus_client.is_forced_to_close(self.uid, 0):
            self.close_button.set_label(self.close_button_text)
            gobject.timeout_add(1000*15, self.__close_the_dialog_by_timeout)

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
        
    def __inventory_toggle(self, widget, data=None):
        if widget.get_active() and data is not None:
            self.buy_time_button.set_sensitive(True)
            self.selected_chore = data

    def __buy_time_button_clicked_cb(self, widget, data):
        if self.dbus_client.contract_chore(int(self.selected_chore[0]), self.uid, int(time.time())):
            print "CONTRACTED A CHORE"
            sys.exit(0)
        else:
            print "Contracting failed"
            self.__close_button_clicked_cb(widget, data)

    def __time_button_clicked_cb(self, widget, data):
        print "TIME BUTTON"

        self.already_closed = True

        self.dbus_client.take_mercy(self.uid, 0)
        gtk.gdk.keyboard_ungrab()
        self.hide()
        
        print "..."
        
        gobject.timeout_add(1000*60*5, self.__timeout_cb)
        
    def __timeout_cb(self):
        print "BACK IN BLOCKER"
        if self.dbus_client.is_allowed_to_use(self.uid, 0):
            sys.exit(0)

        self.show()
        self.__setup_ui(mercy_button=False)
        
        return False

    def __close_button_clicked_cb(self, widget, data):
        """Universal method to close session"""

        self.already_closed = True

        print "CLOSING..."
        if os.name == "nt" :
            windll.user32.ExitWindowsEx(0)
        elif os.name == "posix" :
            try:
                d = dbus.SessionBus()
                smgr_obj = d.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
                session_manager = dbus.Interface(smgr_obj, "org.gnome.SessionManager")
                session_manager.Logout(1)
            except:
                # The following occasionally happens:
                #   DBusException: org.freedesktop.DBus.Error.ServiceUnknown: The name
                #   org.gnome.SessionManager was not provided by any .service files
                
                #print traceback.format_exc()

                self.__close_session_fallback()

        sys.exit(0)

    def __close_the_dialog_by_timeout(self):
        if self.already_closed:
            return False
            
        if self.close_button_countdown >= 0:
        
            if self.close_button_countdown < 30:
                b = self.close_button
                b.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("indianred"))
                l = b.get_children()[0]
                l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))                                                                                             
                l.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse("black"))

            self.close_button.set_label(self.close_button_text + " (%s)" % self.close_button_countdown)
            self.close_button_countdown -= 1
            gobject.timeout_add(1000, self.__close_the_dialog_by_timeout)
            return False
        else:
            self.close_button.set_label(self.close_button_text)
            print "TIMEOUT"
            self.__close_button_clicked_cb(None, None)
            
    def __close_session_fallback(self):
        """Fallback for the moments org.gnome.SessionManager doesn't connect"""
        proclist = gtop.proclist(gtop.PROCLIST_KERN_PROC_UID, int(self.uid))
        for proc in proclist:
            if len(gtop.proc_args(proc))==0:
                continue
            if gtop.proc_args(proc)[0] == "x-session-manager" or gtop.proc_args(proc)[0] == "/usr/bin/x-session-manager" or gtop.proc_args(proc)[0] == "/usr/bin/gnome-session" or gtop.proc_args(proc)[0] == "gnome-session":
                cmd = "kill -9 %s" % (proc)
                print "Executing fallback:", cmd
                Popen(cmd, shell=True, stdout=PIPE)


