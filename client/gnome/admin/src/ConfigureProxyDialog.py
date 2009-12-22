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

class ConfigureProxyDialog (gtk.Dialog):
    def __init__ (self, selected_user_id):
        gtk.Dialog.__init__ (self, title=_("Web Content Filter Configuration"), buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        nanny.client.common.Utils.glade_magic (self,
                glade_file = os.path.join (nanny.client.gnome.admin.glade_files_dir, "nac_wcf_dialog.glade"),
                prefix = "wcfd")

        self.dbus_client = nanny.client.common.DBusClient ()
        self.__selected_user_id = selected_user_id

        self.main_notebook.unparent()
        self.get_content_area().add (self.main_notebook)

        self.blacklist_edit_button.set_no_show_all(True)
        self.whitelist_edit_button.set_no_show_all(True)

        self.blacklist_add_button.connect ('clicked', self.__on_blacklist_add_button_clicked)
        self.blacklist_edit_button.connect ('clicked', self.__on_blacklist_edit_button_clicked)
        self.blacklist_remove_button.connect ('clicked', self.__on_blacklist_remove_button_clicked)
        self.whitelist_add_button.connect ('clicked', self.__on_whitelist_add_button_clicked)
        self.whitelist_edit_button.connect ('clicked', self.__on_whitelist_edit_button_clicked)
        self.whitelist_remove_button.connect ('clicked', self.__on_whitelist_remove_button_clicked)

        self.__init_treeview (self.blacklist_treeview)
        self.__init_treeview (self.whitelist_treeview)
        self.__fill_treeviews ()

        selection = self.blacklist_treeview.get_selection()
        selection.connect ('changed', self.__on_blacklist_selection_changed)
        self.__on_blacklist_selection_changed (selection)
        selection = self.whitelist_treeview.get_selection()
        selection.connect ('changed', self.__on_whitelist_selection_changed)
        self.__on_whitelist_selection_changed (selection)

        self.resize (700, 460)

        self.show_all ()

    def __init_treeview (self, treeview):
        base_id = 0
        for field in ["id", "description"]:
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

        store = gtk.ListStore (gobject.TYPE_INT,
                               gobject.TYPE_STRING)

        treeview.set_model (store)

    def __fill_treeviews (self):
        blacklist_model = self.blacklist_treeview.get_model()
        blacklist_model.clear()

        whitelist_model = self.whitelist_treeview.get_model()
        whitelist_model.clear()

        filters = self.dbus_client.list_filters (self.__selected_user_id)
        for filter_id, filter_name, filter_description, is_black in filters:
            if is_black:
                blacklist_model.append ((filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description)))
            else:
                whitelist_model.append ((filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description)))

    def __on_blacklist_add_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        self.proxy_rule_dialog = xml.get_object ('wcfed_dialog')
        ret = self.proxy_rule_dialog.run()
        if ret == 2:
            combobox = xml.get_object ('wcfed_type_combobox')
            name_entry = xml.get_object ('wcfed_name_entry')
            description_entry = xml.get_object ('wcfed_description_entry')
            url_entry = xml.get_object ('wcfed_url_entry')

            name = name_entry.get_text()
            type = combobox.get_active ()
            description = description_entry.get_text()
            url = url_entry.get_text()

            if type == 0:
                self.progress_dialog = ProgressDialog (_("Downloading the list. Please, wait..."))
                self.dbus_client.add_dansguardian_list (self.__selected_user_id,
                                                        name,
                                                        description,
                                                        url,
                                                        self.__on_add_dansguardian_list_reply,
                                                        self.__on_add_dansguardian_list_error)
            elif type == 1:
                self.dbus_client.add_custom_filter (self.__selected_user_id, True, name, description, url)
                self.__fill_treeviews ()
                self.proxy_rule_dialog.destroy()
                self.proxy_rule_dialog = None
        else:
            self.proxy_rule_dialog.destroy()
            self.proxy_rule_dialog = None
        
        
    def __on_whitelist_add_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        dialog = xml.get_object ('wcfed_dialog')

        type_label = xml.get_object ('wcfed_type_label')
        type_label.hide()
        combobox = xml.get_object ('wcfed_type_combobox')
        combobox.hide()

        dialog = xml.get_object ('wcfed_dialog')
        ret = dialog.run()
        if ret == 2:
            name_entry = xml.get_object ('wcfed_name_entry')
            description_entry = xml.get_object ('wcfed_description_entry')
            url_entry = xml.get_object ('wcfed_url_entry')

            name = name_entry.get_text()
            description = description_entry.get_text()
            url = url_entry.get_text()

            self.dbus_client.add_custom_filter (self.__selected_user_id, False, name, description, url)

            self.__fill_treeviews ()
        
        dialog.destroy()

    def __on_add_dansguardian_list_reply (self, value):
        self.progress_dialog.destroy()
        self.progress_dialog = None

        if value:
            self.__fill_treeviews ()
            if self.proxy_rule_dialog != None:
                self.proxy_rule_dialog.destroy()
                self.proxy_rule_dialog = None
        else:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dlg.set_markup(_("<b>Error while importing list from the Internet</b>"))
            dlg.format_secondary_markup(_("Some error has occured while downloading the list.\nPlease verify the URL and try again."))
            dlg.run()
            dlg.destroy()

    def __on_add_dansguardian_list_error (self, exception):
        self.progress_dialog.destroy()
        self.progress_dialog = None

        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dlg.set_markup(_("<b>Error while importing list from the Internet</b>"))
        dlg.format_secondary_markup(_("Some error has occured while downloading the list.\nPlease verify the URL and try again."))
        dlg.run()
        dlg.destroy()

    def __on_blacklist_edit_button_clicked (self, widget, data=None):
        pass

    def __on_whitelist_edit_button_clicked (self, widget, data=None):
        pass

    def __on_blacklist_remove_button_clicked (self, widget, data=None):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK_CANCEL)
        dlg.set_markup(_("<b>Are you sure you want to delete this filter?</b>"))
        dlg.format_secondary_markup(_("You will not be able to undo this action."))
        ret = dlg.run()
        dlg.destroy()
        
        if ret != gtk.RESPONSE_OK:
            return

        selection = self.blacklist_treeview.get_selection()
        if selection.count_selected_rows () > 0:
            self.progress_dialog = ProgressDialog (_("Downloading the list. Please, wait..."))
            model, paths = selection.get_selected_rows()
            if paths:
                for path in paths:
                    id = model.get_value (model.get_iter(path), 0)
                    self.dbus_client.remove_filter (id,
                                                    self.__on_remove_filter_reply,
                                                    self.__on_remove_filter_error)

        self.__fill_treeviews ()

    def __on_whitelist_remove_button_clicked (self, widget, data=None):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK_CANCEL)
        dlg.set_markup(_("<b>Are you sure you want to delete this filter?</b>"))
        dlg.format_secondary_markup(_("You will not be able to undo this action."))
        ret = dlg.run()
        dlg.destroy()
        
        if ret != gtk.RESPONSE_OK:
            return

        selection = self.whitelist_treeview.get_selection()
        if selection.count_selected_rows () > 0:
            self.progress_dialog = ProgressDialog (_("Downloading the list. Please, wait..."))
            model, paths = selection.get_selected_rows()
            if paths:
                for path in paths:
                    id = model.get_value (model.get_iter(path), 0)
                    self.dbus_client.remove_filter (id,
                                                    self.__on_remove_filter_reply,
                                                    self.__on_remove_filter_error)

        self.__fill_treeviews ()

    def __on_remove_filter_reply (self, value):
        self.progress_dialog.destroy()
        self.progress_dialog = None

        if value:
            self.__fill_treeviews ()
        else:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dlg.set_markup(_("<b>Error while deleting filters</b>"))
            dlg.format_secondary_markup(_("Some error has occured while deleting filters.\nPlease try again."))
            dlg.run()
            dlg.destroy()

    def __on_remove_filter_error (self, exception):
        self.progress_dialog.destroy()
        self.progress_dialog = None

        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dlg.set_markup(_("<b>Error while deleting filters</b>"))
        dlg.format_secondary_markup(_("Some error has occured while deleting filters.\nPlease try again."))
        dlg.run()
        dlg.destroy()

    def __on_blacklist_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.blacklist_edit_button.set_sensitive (True)
            self.blacklist_remove_button.set_sensitive (True)
        else:
            self.blacklist_edit_button.set_sensitive (False)
            self.blacklist_remove_button.set_sensitive (False)

    def __on_whitelist_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.whitelist_edit_button.set_sensitive (True)
            self.whitelist_remove_button.set_sensitive (True)
        else:
            self.whitelist_edit_button.set_sensitive (False)
            self.whitelist_remove_button.set_sensitive (False)

    def __load_dialog (self):
        glade_file = os.path.join (nanny.client.gnome.admin.glade_files_dir, "nac_wcf_edit_dialog.glade")
        xml = gtk.Builder ()
        xml.add_from_file (glade_file)

        store = gtk.ListStore (gobject.TYPE_INT, gobject.TYPE_STRING)
        store.append ((0, _("Download list from the Internet")))
        store.append ((1, _("Insert manual URL")))

        combobox = xml.get_object ('wcfed_type_combobox')
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.set_model (store)
        combobox.set_active (0)

        return xml

class ProgressDialog (gtk.Window):
    def __init__ (self, text):
        gtk.Window.__init__ (self)

        self.set_decorated (False)
        self.resize (150, 50)
        self.set_position (gtk.WIN_POS_CENTER)
        self.set_modal (True)

        self.progressbar = gtk.ProgressBar ()
        self.progressbar.set_text (text)

        self.timer = gobject.timeout_add (100, self.progress_timeout)

        self.add (self.progressbar)

        self.show_all()

    def progress_timeout (self):
        self.progressbar.pulse ()
        return True
