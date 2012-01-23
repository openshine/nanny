#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2009 Junta de Andalucia
# Copyright (C) 2012 Guido Tabbernuk
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
#   Cesar Garcia Tapia <cesar.garcia.tapia at openshine.com>
#   Luis de Bethencourt <luibg at openshine.com>
#   Pablo Vieytes <pvieytes at openshine.com>
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

import gtk
import pango
import gobject

import nanny

class BlacklistManager:
    def __init__ (self):
        self.dialog = gtk.Dialog (title=_("Blacklist Filter Configuration"), buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        nanny.client.common.Utils.ui_magic (self,
                ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nbm_pbl_dialog.ui"),
                prefix = "nbm")

        self.dialog.set_property("icon-name", "nanny")
        self.dbus_client = nanny.client.common.DBusClient ()

        self.alignment.unparent ()
        self.dialog.get_content_area().add (self.alignment)

        self.blacklist_import_button.connect ('clicked', self.__on_blacklist_import_button_clicked)
        self.blacklist_update_button.connect ('clicked', self.__on_blacklist_update_button_clicked)
        self.blacklist_remove_button.connect ('clicked', self.__on_blacklist_remove_button_clicked)
        self.unlock_button.connect('clicked', self.__on_unlock_button_clicked)

        self.__selected_blacklist = None

        self.__init_treeview (self.blacklist_treeview)
        self.__fill_treeview ()

        selection = self.blacklist_treeview.get_selection()
        selection.connect ('changed', self.__on_blacklist_selection_changed)
        self.__on_blacklist_selection_changed (selection)

        self.dialog.resize (700, 460)
        
        self.__lock_widgets()
        self.dialog.run ()
        self.dialog.destroy()

    def __init_treeview (self, treeview):
        base_id = 1 
        for field in ["id", "name"]:
            col = gtk.TreeViewColumn(field)
            treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'markup', base_id)
            if field != "id":
                col.set_visible (True)
            else:
                col.set_visible (False)
            
            base_id = base_id + 1

        store = gtk.ListStore (gobject.TYPE_BOOLEAN,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)

    def __lock_widgets(self) :
        lock_status = self.dbus_client.is_unlocked()
        if lock_status == True :
            self.unlock_area.hide()
        else:
            self.unlock_area.show()

        self.blacklist_import_button.set_sensitive(lock_status)
        self.blacklist_update_button.set_sensitive(lock_status)
        self.blacklist_remove_button.set_sensitive(lock_status)
        

    def __fill_treeview (self):
        model = self.blacklist_treeview.get_model()
        model.clear()

        filters = self.dbus_client.list_pkg_filters ()
        for filter_id, read_only in filters:
            filter_name, filter_description = self.dbus_client.get_pkg_filter_metadata(filter_id)

            if read_only:
                model.append ((read_only, filter_id, _("<b>%s (Read only)</b>\n   %s") % (filter_name, filter_description)))
            else:
                model.append ((read_only, filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description)))

    def __on_blacklist_import_button_clicked (self, widget, data=None):
	dialog = gtk.MessageDialog(
		None,
		gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
		gtk.MESSAGE_QUESTION,
		gtk.BUTTONS_OK,
		None)

        def responseToDialog(entry, dialog, response):
            dialog.response(response)

	dialog.set_markup('Enter blacklist repository URL')
	entry = gtk.Entry()
	entry.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
	hbox = gtk.HBox()
	hbox.pack_start(gtk.Label("Url:"), False, 5, 5)
	hbox.pack_end(entry)
	dialog.format_secondary_markup("It's something like http://static.nannycentral.org/v/nannycentral/blacklists/blacklist.json")
	dialog.vbox.pack_end(hbox, True, True, 0)
	dialog.show_all()
	dialog.run()
	text = entry.get_text()
	dialog.destroy()
        
        if not text.startswith("http:/") :
            text = "http://" + text

        result = self.dbus_client.add_pkg_filter (text)

    def __on_blacklist_update_button_clicked (self, widget, data=None):
        pass

    def __on_blacklist_remove_button_clicked (self, widget, data=None):
        if self.__selected_blacklist == None:
            return

        d = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL)
        d.set_property("icon-name", "nanny")
        d.set_markup(_("<b>Are you sure you want to delete this blacklist?</b>"))
        d.format_secondary_markup(_("This action will remove all the user configuration linked to the blacklist."))
        response = d.run()
        if response == gtk.RESPONSE_OK:
            self.dbus_client.remove_pkg_filter (self.__selected_blacklist)
            self.__fill_treeview ()

        d.destroy()

    def __on_blacklist_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            model, itera = selection.get_selected ()
            self.__selected_blacklist = model.get_value (itera, 1)
            read_only = model.get_value (itera, 0)

            if read_only:
                self.blacklist_remove_button.set_sensitive (False)
            else:
                self.blacklist_remove_button.set_sensitive (True)

        else:
            self.blacklist_remove_button.set_sensitive (False)
            self.__selected_blacklist = None

    def __on_unlock_button_clicked (self, widget, data=None):
        self.dbus_client.unlock()
        self.__lock_widgets()
