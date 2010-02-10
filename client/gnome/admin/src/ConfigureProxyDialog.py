#!/usr/bin/python
# -*- coding: utf-8 -*-

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

import gtk
import pango
import gobject

import nanny

class ConfigureProxyDialog (gtk.Dialog):
    def __init__ (self, selected_user_id):
        gtk.Dialog.__init__ (self, title=_("Web Content Filter Configuration"), buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        nanny.client.common.Utils.ui_magic (self,
                ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nac_wcf_dialog.ui"),
                prefix = "wcfd")

        self.set_property("icon-name", "nanny")
        self.dbus_client = nanny.client.common.DBusClient ()
        self.__selected_user_id = selected_user_id

        self.main_notebook.unparent()
        self.get_content_area().add (self.main_notebook)

        self.custom_blacklist_add_button.connect ('clicked', self.__on_custom_blacklist_add_button_clicked)
        self.custom_blacklist_edit_button.connect ('clicked', self.__on_custom_blacklist_edit_button_clicked)
        self.custom_blacklist_remove_button.connect ('clicked', self.__on_custom_blacklist_remove_button_clicked)
        self.custom_whitelist_add_button.connect ('clicked', self.__on_custom_whitelist_add_button_clicked)
        self.custom_whitelist_edit_button.connect ('clicked', self.__on_custom_whitelist_edit_button_clicked)
        self.custom_whitelist_remove_button.connect ('clicked', self.__on_custom_whitelist_remove_button_clicked)

        self.__init_custom_treeview (self.custom_blacklist_treeview)
        self.__init_custom_treeview (self.custom_whitelist_treeview)
        self.__init_pkg_treeview (self.packaged_blacklist_treeview)
        self.__init_pkg_categories_treeview (self.packaged_blacklist_categories_treeview)
        self.__fill_treeviews ()

        selection = self.custom_blacklist_treeview.get_selection()
        selection.connect ('changed', self.__on_custom_blacklist_selection_changed)
        self.__on_custom_blacklist_selection_changed (selection)

        selection = self.custom_whitelist_treeview.get_selection()
        selection.connect ('changed', self.__on_custom_whitelist_selection_changed)
        self.__on_custom_whitelist_selection_changed (selection)

        selection = self.packaged_blacklist_treeview.get_selection()
        selection.connect ('changed', self.__on_packaged_blacklist_selection_changed)
        self.__on_packaged_blacklist_selection_changed (selection)

        self.resize (700, 460)

        self.show_all ()

    def __init_custom_treeview (self, treeview):
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
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)

    def __init_pkg_treeview (self, treeview):
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

        store = gtk.ListStore (gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)

    def __init_pkg_categories_treeview (self, treeview):
        base_id = 0
        for field in ["selected", "description"]:
            col = gtk.TreeViewColumn(field)
            treeview.append_column(col)
            if field == "description":
                cell = gtk.CellRendererText()
                cell.set_property("ellipsize", pango.ELLIPSIZE_END)
                col.pack_start(cell, True)
                col.add_attribute(cell, 'markup', base_id)
            else:
                cell = gtk.CellRendererToggle()
                cell.connect( 'toggled', self.__on_packaged_blacklist_categories_toggled)
                col.pack_start(cell, True)
                col.add_attribute(cell, 'active', base_id)
                col.add_attribute (cell, 'activatable', True)

            col.set_visible (True)
            
            base_id = base_id + 1

        store = gtk.ListStore (gobject.TYPE_BOOLEAN,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)

    def __fill_treeviews (self):
        custom_blacklist_model = self.custom_blacklist_treeview.get_model()
        custom_blacklist_model.clear()

        custom_whitelist_model = self.custom_whitelist_treeview.get_model()
        custom_whitelist_model.clear()

        packaged_blacklist_model = self.packaged_blacklist_treeview.get_model()
        packaged_blacklist_model.clear()

        filters = self.dbus_client.list_custom_filters (self.__selected_user_id)
        for filter_id, filter_name, filter_description, filter_regex, is_black in filters:
            if is_black:
                custom_blacklist_model.append ((filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description), filter_name, filter_description, filter_regex))
            else:
                custom_whitelist_model.append ((filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description), filter_name, filter_description, filter_regex))

        pkg_filters = self.dbus_client.list_pkg_filters ()
        for filter_id, readonly in pkg_filters:
            filter_name, filter_description = self.dbus_client.get_pkg_filter_metadata(filter_id)
            packaged_blacklist_model.append ((filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description)))

    def __on_custom_blacklist_add_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        self.proxy_rule_dialog = xml.get_object ('wcfed_dialog')
        warning_label = xml.get_object ("wcfed_warning_label")
        warning_label.hide ()
        while True:
            ret = self.proxy_rule_dialog.run()
            if ret == 2:
                name_entry = xml.get_object ('wcfed_name_entry')
                description_entry = xml.get_object ('wcfed_description_entry')
                url_entry = xml.get_object ('wcfed_url_entry')

                name = name_entry.get_text().strip()
                description = description_entry.get_text().strip()
                url = url_entry.get_text().strip()

                if name == "" or description == "" or url == "":
                    warning_label.show()
                    continue

                self.dbus_client.add_custom_filter (self.__selected_user_id, True, name, description, url)
                self.__fill_treeviews ()
                self.proxy_rule_dialog.destroy()
                break
            else:
                self.proxy_rule_dialog.destroy()
                break
        
    def __on_custom_whitelist_add_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        dialog = xml.get_object ('wcfed_dialog')
        warning_label = xml.get_object ("wcfed_warning_label")
        warning_label.hide ()

        while True:
            ret = dialog.run()
            if ret == 2:
                name_entry = xml.get_object ('wcfed_name_entry')
                description_entry = xml.get_object ('wcfed_description_entry')
                url_entry = xml.get_object ('wcfed_url_entry')

                name = name_entry.get_text().strip()
                description = description_entry.get_text().strip()
                url = url_entry.get_text().strip()

                if name == "" or description == "" or url == "":
                    warning_label.show()
                    continue

                self.dbus_client.add_custom_filter (self.__selected_user_id, False, name, description, url)
                self.__fill_treeviews ()
                dialog.destroy()
                break
            else:
                dialog.destroy()
                break

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
            dlg.set_property("icon-name", "nanny")
            dlg.set_markup("<b>%s</b>" % _("Error while importing list from the Internet"))
            dlg.format_secondary_markup(_("Some error has occured while downloading the list.\nPlease verify the URL and try again."))
            dlg.run()
            dlg.destroy()

    def __on_add_dansguardian_list_error (self, exception):
        self.progress_dialog.destroy()
        self.progress_dialog = None

        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dlg.set_property("icon-name", "nanny")
        dlg.set_markup("<b>%s</b>" % _("Error while importing list from the Internet"))
        dlg.format_secondary_markup(_("Some error has occured while downloading the list.\nPlease verify the URL and try again."))
        dlg.run()
        dlg.destroy()

    def __on_custom_blacklist_edit_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        self.proxy_rule_dialog = xml.get_object ('wcfed_dialog')
        warning_label = xml.get_object ("wcfed_warning_label")
        warning_label.hide ()

        name_entry = xml.get_object ('wcfed_name_entry')
        description_entry = xml.get_object ('wcfed_description_entry')
        url_entry = xml.get_object ('wcfed_url_entry')

        selection = self.custom_blacklist_treeview.get_selection()
        if selection.count_selected_rows () > 0:
            model, iter = selection.get_selected()
            if iter:
                filter_id = model.get_value (iter, 0)
                filter_name = model.get_value (iter, 2)
                filter_description = model.get_value (iter, 3)
                filter_regex = model.get_value (iter, 4)

                name_entry.set_text (filter_name)
                description_entry.set_text (filter_description)
                url_entry.set_text (filter_regex)

        while True:
            ret = self.proxy_rule_dialog.run()
            if ret == 2:
                filter_name = name_entry.get_text().strip()
                filter_description = description_entry.get_text().strip()
                filter_url = url_entry.get_text().strip()

                if filter_name == "" or filter_description == "" or filter_url == "":
                    warning_label.show()
                    continue

                self.dbus_client.update_custom_filter (filter_id, filter_name, filter_description, filter_url)
                self.__fill_treeviews ()
                self.proxy_rule_dialog.destroy()
                break
            else:
                self.proxy_rule_dialog.destroy()
                break

    def __on_custom_whitelist_edit_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        self.proxy_rule_dialog = xml.get_object ('wcfed_dialog')
        warning_label = xml.get_object ("wcfed_warning_label")
        warning_label.hide ()

        name_entry = xml.get_object ('wcfed_name_entry')
        description_entry = xml.get_object ('wcfed_description_entry')
        url_entry = xml.get_object ('wcfed_url_entry')

        selection = self.custom_whitelist_treeview.get_selection()
        if selection.count_selected_rows () > 0:
            model, iter = selection.get_selected()
            if iter:
                filter_id = model.get_value (iter, 0)
                filter_name = model.get_value (iter, 2)
                filter_description = model.get_value (iter, 3)
                filter_regex = model.get_value (iter, 4)

                name_entry.set_text (filter_name)
                description_entry.set_text (filter_description)
                url_entry.set_text (filter_regex)

        while True:
            ret = self.proxy_rule_dialog.run()
            if ret == 2:
                filter_name = name_entry.get_text().strip()
                filter_description = description_entry.get_text().strip()
                filter_url = url_entry.get_text().strip()

                if filter_name == "" or filter_description == "" or filter_url == "":
                    warning_label.show()
                    continue

                self.dbus_client.update_custom_filter (filter_id, filter_name, filter_description, filter_url)
                self.__fill_treeviews ()
                self.proxy_rule_dialog.destroy()
                break
            else:
                self.proxy_rule_dialog.destroy()
                break

    def __on_custom_blacklist_remove_button_clicked (self, widget, data=None):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK_CANCEL)
        dlg.set_property("icon-name", "nanny")
        dlg.set_markup("<b>%s</b>" % _("Are you sure you want to delete this filter?"))
        dlg.format_secondary_markup(_("You will not be able to undo this action."))
        ret = dlg.run()
        dlg.destroy()
        
        if ret != gtk.RESPONSE_OK:
            return

        self.progress_dialog = ProgressDialog (_("Removing filter. Please, wait..."))
        selection = self.custom_blacklist_treeview.get_selection()
        if selection.count_selected_rows () > 0:
            model, iter = selection.get_selected()
            if iter:
                id = model.get_value (iter, 0)
                self.dbus_client.remove_custom_filter (id,
                                                       self.__on_remove_filter_reply,
                                                       self.__on_remove_filter_error)

    def __on_custom_whitelist_remove_button_clicked (self, widget, data=None):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK_CANCEL)
        dlg.set_property("icon-name", "nanny")
        dlg.set_markup("<b>%s</b>" % _("Are you sure you want to delete this filter?"))
        dlg.format_secondary_markup(_("You will not be able to undo this action."))
        ret = dlg.run()
        dlg.destroy()
        
        if ret != gtk.RESPONSE_OK:
            return

        self.progress_dialog = ProgressDialog (_("Removing filter. Please, wait..."))
        selection = self.custom_whitelist_treeview.get_selection()
        if selection.count_selected_rows () > 0:
            model, iter = selection.get_selected()
            if iter:
                id = model.get_value (iter, 0)
                self.dbus_client.remove_custom_filter (id,
                                                       self.__on_remove_filter_reply,
                                                       self.__on_remove_filter_error)

    def __on_remove_filter_reply (self, value):
        self.progress_dialog.destroy()
        self.progress_dialog = None

        if value:
            self.__fill_treeviews ()
        else:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dlg.set_property("icon-name", "nanny")
            dlg.set_markup("<b>%s</b>" % _("Error while deleting filters"))
            dlg.format_secondary_markup(_("Some error has occured while deleting filters.\nPlease try again."))
            dlg.run()
            dlg.destroy()

    def __on_remove_filter_error (self, exception):
        self.progress_dialog.destroy()
        self.progress_dialog = None

        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dlg.set_property("icon-name", "nanny")
        dlg.set_markup("<b>%s</b>" % _("Error while deleting filters"))
        dlg.format_secondary_markup(_("Some error has occured while deleting filters.\nPlease try again."))
        dlg.run()
        dlg.destroy()

    def __on_custom_blacklist_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.custom_blacklist_edit_button.set_sensitive (True)
            self.custom_blacklist_remove_button.set_sensitive (True)
        else:
            self.custom_blacklist_edit_button.set_sensitive (False)
            self.custom_blacklist_remove_button.set_sensitive (False)

    def __on_custom_whitelist_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.custom_whitelist_edit_button.set_sensitive (True)
            self.custom_whitelist_remove_button.set_sensitive (True)
        else:
            self.custom_whitelist_edit_button.set_sensitive (False)
            self.custom_whitelist_remove_button.set_sensitive (False)

    def __on_packaged_blacklist_selection_changed (self, selection, data=None):
        packaged_blacklist_categories_model = self.packaged_blacklist_categories_treeview.get_model()
        packaged_blacklist_categories_model.clear()

        if selection.count_selected_rows () > 0:
            model, iter = selection.get_selected()
            if iter:
                self.selected_packaged_filter_id = model.get_value (iter, 0)

                categories = self.dbus_client.get_pkg_filter_user_categories (self.selected_packaged_filter_id, self.__selected_user_id) 
                if len (categories) > 0:
                    packaged_blacklist_categories_model.append ((False, _('<b>Select all the categories</b>'), 'ALL'))

                for category, user_category in categories:
                    if category in nanny.client.common.Categories.category_strings:
                        category_name, category_description = nanny.client.common.Categories.category_strings[category]
                        packaged_blacklist_categories_model.append ((user_category, "%s - %s" % (category_name, category_description), category))
                    else:
                        packaged_blacklist_categories_model.append ((user_category, category, category))
            else:
                self.selected_packaged_filter_id = None
        else:
            self.selected_packaged_filter_id = None
    
    def __on_packaged_blacklist_categories_toggled (self, cell, path, data=None):
        packaged_blacklist_categories_model = self.packaged_blacklist_categories_treeview.get_model()
        packaged_blacklist_categories_model[path][0] = not packaged_blacklist_categories_model[path][0]

        active_categories = []
        is_all_cell = packaged_blacklist_categories_model[path][2] == 'ALL'
        if is_all_cell:
            check_all_cells = packaged_blacklist_categories_model[path][0]
            packaged_blacklist_categories_model.foreach (self.__check_all_packaged_blacklist_categories, (check_all_cells, active_categories))
        else:
            packaged_blacklist_categories_model.foreach (self.__get_packaged_blacklist_categories, active_categories)

        self.dbus_client.set_pkg_filter_user_categories (self.selected_packaged_filter_id, self.__selected_user_id, active_categories)

    def __check_all_packaged_blacklist_categories (self, model, path, iter, data=None):
        check_all_cells, active_categories = data
        model[path][0] = check_all_cells 
        if check_all_cells:
            category_name = model[path][2]
            active_categories.append (category_name)

    def __get_packaged_blacklist_categories (self, model, path, iter, active_categories):
        category_active = model.get_value (iter, 0)
        category_name = model.get_value (iter, 2)

        if category_active:
            active_categories.append (category_name)

    def __load_dialog (self):
        ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nac_wcf_edit_dialog.ui")
        xml = gtk.Builder ()
        xml.add_from_file (ui_file)

        return xml

class ProgressDialog (gtk.Window):
    def __init__ (self, text):
        gtk.Window.__init__ (self)

        self.set_property("icon-name", "nanny")
        self.set_title(text)
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
