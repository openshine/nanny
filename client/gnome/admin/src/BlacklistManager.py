#!/usr/bin/python
# -*- coding: utf-8 -*-

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
        self.blacklist_edit_button.connect ('clicked', self.__on_blacklist_edit_button_clicked)
        self.blacklist_remove_button.connect ('clicked', self.__on_blacklist_remove_button_clicked)

        self.__selected_blacklist = None

        self.__init_treeview (self.blacklist_treeview)
        self.__fill_treeview ()

        selection = self.blacklist_treeview.get_selection()
        selection.connect ('changed', self.__on_blacklist_selection_changed)
        self.__on_blacklist_selection_changed (selection)

        self.dialog.resize (700, 460)

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
        file_selection_dialog = gtk.FileChooserDialog (_("Select file to import"), self.dialog,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        file_selection_dialog.set_select_multiple (False)

        file_filter = gtk.FileFilter ()
        file_filter.add_pattern ("*.nbl")

        file_selection_dialog.set_filter (file_filter)
        response = file_selection_dialog.run()

        if response == gtk.RESPONSE_ACCEPT:
            filename = file_selection_dialog.get_filename()
            result = self.dbus_client.add_pkg_filter (filename)
            
            if result:
                self.__fill_treeview ()
            else:
                d = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
                d.set_property("icon-name", "nanny")
                d.set_markup(_("<b>Error importing blacklist file</b>"))
                d.format_secondary_markup(_("Some error has occured importing the blacklist file."))
                d.run()
                d.destroy()

        file_selection_dialog.destroy()

    def __on_blacklist_edit_button_clicked (self, widget, data=None):
        edit_dialog = gtk.Dialog (title=_("Blacklist Filter Configuration"),
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        nanny.client.common.Utils.ui_magic (edit_dialog,
                                  ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nbm_pbl_edit_dialog.ui"),
                                  prefix = "nbm")

        edit_dialog.main_alignment.unparent()
        edit_dialog.get_content_area().add (edit_dialog.main_alignment)

        name, description = self.dbus_client.get_pkg_filter_metadata (self.__selected_blacklist)
        edit_dialog.name_entry.set_text (name)
        edit_dialog.description_entry.set_text (description)

        response = edit_dialog.run()

        if response == gtk.RESPONSE_ACCEPT:
            name = edit_dialog.name_entry.get_text ()
            description = edit_dialog.description_entry.get_text ()
            self.dbus_client.set_pkg_filter_metadata (self.__selected_blacklist, name, description)
            self.__fill_treeview ()

        edit_dialog.destroy()

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
                self.blacklist_edit_button.set_sensitive (False)
                self.blacklist_remove_button.set_sensitive (False)
            else:
                self.blacklist_edit_button.set_sensitive (True)
                self.blacklist_remove_button.set_sensitive (True)

        else:
            self.blacklist_edit_button.set_sensitive (False)
            self.blacklist_remove_button.set_sensitive (False)
            self.__selected_blacklist = None
