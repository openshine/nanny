#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2009,2010 Junta de Andalucia
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

class ConfigureProxyDialog (gtk.Dialog):
    def __init__ (self, selected_user_id, proxies_enabled):
        gtk.Dialog.__init__ (self, title=_("Web Content Filter Configuration"), buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.proxies_enabled = proxies_enabled

        nanny.client.common.Utils.ui_magic (self,
                ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nac_wcf_dialog.ui"),
                prefix = "wcfd")

        self.set_property("icon-name", "nanny")
        self.dbus_client = nanny.client.common.DBusClient ()
        self.__selected_user_id = selected_user_id

        self.main_vbox.unparent()
        self.get_content_area().add (self.main_vbox)

        self.browser_use_proxy_checkbutton.set_active(self.proxies_enabled)
        self.browser_use_proxy_checkbutton.connect('toggled', self.__on_browser_use_proxy_checkbutton_toggled)

        self.custom_blacklist_add_button.connect ('clicked', self.__on_custom_blacklist_add_button_clicked)
        self.custom_blacklist_edit_button.connect ('clicked', self.__on_custom_blacklist_edit_button_clicked)
        self.custom_blacklist_remove_button.connect ('clicked', self.__on_custom_blacklist_remove_button_clicked)
        self.custom_whitelist_add_button.connect ('clicked', self.__on_custom_whitelist_add_button_clicked)
        self.custom_whitelist_edit_button.connect ('clicked', self.__on_custom_whitelist_edit_button_clicked)
        self.custom_whitelist_remove_button.connect ('clicked', self.__on_custom_whitelist_remove_button_clicked)

        self.add_bl_button.connect("clicked", self.__on_add_bl_button_cb)
        self.del_bl_button.connect("clicked", self.__on_del_bl_button_cb)
        self.update_bl_button.connect("clicked", self.__on_update_bl_button_cb)

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

    def run(self):
        super(ConfigureProxyDialog, self).run()
        
        return self.proxies_enabled

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
        
        
        for filter_id in self.dbus_client.list_pkg_filters () :
            metadata = self.dbus_client.get_pkg_filter_metadata(filter_id)
            filter_name = _("Unknown Blacklist Name") if not metadata.has_key("name") else metadata["name"]
            filter_description = "" if not metadata.has_key("provider") else metadata["provider"]
            
            packaged_blacklist_model.append ((filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description)))

        gobject.timeout_add(1, self.__update_packaged_blacklist_model)

    def __update_packaged_blacklist_model(self):
        try:
            list_store =  self.packaged_blacklist_treeview.get_model()
            server_list =  self.dbus_client.list_pkg_filters () 
            
            for filter_id in server_list:
                included = False
                for row in list_store:
                    if row[0] == filter_id :
                        metadata = self.dbus_client.get_pkg_filter_metadata(filter_id)
                        filter_name = _("Unknown Blacklist Name") if not metadata.has_key("name") else metadata["name"]
                        filter_description = "" if not metadata.has_key("provider") else metadata["provider"]
                        filter_description = filter_description + " " + _("(version : %s)" % metadata["release-number"])
                        if metadata.has_key("status") and  metadata.has_key("progress") :
                            if metadata["status"] == 1:
                                filter_description = "<b>" + _("There is an update available") + "</b>"
                            if metadata["status"] == 2:
                                filter_description = _("Downloading information (%s%%)" % metadata["progress"])
                            elif metadata["status"] == 3:
                                filter_description = _("Installing blacklist (%s%%)" % metadata["progress"])
                            elif metadata["status"] == 4:
                                filter_description = _("Updating blacklist (%s%%)" % metadata["progress"])

                        row[1] = "<b>%s</b>\n   <small>%s</small>" % (filter_name, filter_description)
                        included = True
                        break
                
                if included == True:
                    continue

                metadata = self.dbus_client.get_pkg_filter_metadata(filter_id)
                filter_name = _("Unknown Blacklist Name") if not metadata.has_key("name") else metadata["name"]
                filter_description = "" if not metadata.has_key("provider") else metadata["provider"]

                list_store.append ((filter_id, "<b>%s</b>\n   %s" % (filter_name, filter_description)))
            
            iter = list_store.get_iter_first()
            while iter :
                id = list_store.get_value(iter, 0)

                to_remove = True
                for filter_id in server_list:
                    if filter_id == id :
                        to_remove = False
                        break
                
                if to_remove == True :
                    tmp_iter = iter 
                    iter = list_store.iter_next(tmp_iter)
                    list_store.remove(tmp_iter)
                    continue

                iter = list_store.iter_next(iter)

            selection = self.packaged_blacklist_treeview.get_selection()
            if selection.count_selected_rows () > 0:
                self.del_bl_button.set_sensitive(True)
                model, iter = selection.get_selected()
                pkg_id = model.get_value (iter, 0)
                metadata = self.dbus_client.get_pkg_filter_metadata(pkg_id)
                if metadata.has_key("status") and metadata["status"] == 1 :
                    self.update_bl_button.set_sensitive(True)
                else:
                    self.update_bl_button.set_sensitive(False)
            else:
                self.del_bl_button.set_sensitive(False)
                self.update_bl_button.set_sensitive(False)   

            gobject.timeout_add(2000, self.__update_packaged_blacklist_model)
            return False
        except:
            return False

    def __on_entry_dialog_essential_values_changed(self, widget, ok_button, name_entry, description_entry, url_entry):
        """Used for entry dialog value checking, disables "Ok" button when values are not acceptable"""
        
        name = name_entry.get_text().strip()
        description = description_entry.get_text().strip()
        url = url_entry.get_text().strip()
        
        if name == "" or description == "" or url == "":
            ok_button.set_sensitive (False)
        else:
            ok_button.set_sensitive (True)

    def __on_custom_blacklist_add_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        self.proxy_rule_dialog = xml.get_object ('wcfed_dialog')
        self.proxy_rule_dialog.set_title(_("Add blacklist entry"))
        self.proxy_rule_dialog.set_transient_for(self)
        warning_label = xml.get_object ("wcfed_warning_label")
        ok_button = xml.get_object ('wcfed_ok_button')
        name_entry = xml.get_object ('wcfed_name_entry')
        description_entry = xml.get_object ('wcfed_description_entry')
        url_entry = xml.get_object ('wcfed_url_entry')
        
        name_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        description_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        url_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        
        ret = self.proxy_rule_dialog.run()
        if ret == 2:

            name = name_entry.get_text().strip()
            description = description_entry.get_text().strip()
            url = url_entry.get_text().strip()

            self.dbus_client.add_custom_filter (self.__selected_user_id, True, name, description, url)
            self.__fill_treeviews ()
            
        self.proxy_rule_dialog.destroy()
        
    def __on_custom_whitelist_add_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        dialog = xml.get_object ('wcfed_dialog')
        dialog.set_title(_("Add whitelist entry"))        
        dialog.set_transient_for(self)
        ok_button = xml.get_object ('wcfed_ok_button')
        warning_label = xml.get_object ("wcfed_warning_label")
        name_entry = xml.get_object ('wcfed_name_entry')
        description_entry = xml.get_object ('wcfed_description_entry')
        url_entry = xml.get_object ('wcfed_url_entry')

        name_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        description_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        url_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        
        ret = dialog.run()
        if ret == 2:

            name = name_entry.get_text().strip()
            description = description_entry.get_text().strip()
            url = url_entry.get_text().strip()

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
        self.proxy_rule_dialog.set_title(_("Edit custom blacklist entry"))
        self.proxy_rule_dialog.set_transient_for(self)
        ok_button = xml.get_object ('wcfed_ok_button')
        warning_label = xml.get_object ("wcfed_warning_label")
        name_entry = xml.get_object ('wcfed_name_entry')
        description_entry = xml.get_object ('wcfed_description_entry')
        url_entry = xml.get_object ('wcfed_url_entry')

        name_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        description_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)
        url_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, name_entry, description_entry, url_entry)

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

        ret = self.proxy_rule_dialog.run()
        if ret == 2:
            filter_name = name_entry.get_text().strip()
            filter_description = description_entry.get_text().strip()
            filter_url = url_entry.get_text().strip()

            self.dbus_client.update_custom_filter (filter_id, filter_name, filter_description, filter_url)
            self.__fill_treeviews ()
            
        self.proxy_rule_dialog.destroy()

    def __on_custom_whitelist_edit_button_clicked (self, widget, data=None):
        xml = self.__load_dialog ()
        self.proxy_rule_dialog = xml.get_object ('wcfed_dialog')
        self.proxy_rule_dialog.set_transient_for(self)
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
        dlg.set_transient_for(self)
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
        dlg.set_transient_for(self)
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
            self.del_bl_button.set_sensitive(True)

            model, iter = selection.get_selected()
            if iter:
                pkg_id = model.get_value (iter, 0)
                self.selected_packaged_filter_id = pkg_id
                metadata = self.dbus_client.get_pkg_filter_metadata(pkg_id)
                if metadata.has_key("status") and metadata["status"] == 1 :
                    self.update_bl_button.set_sensitive(True)
                else:
                    self.update_bl_button.set_sensitive(False)

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
            self.del_bl_button.set_sensitive(False)
            self.update_bl_button.set_sensitive(False)
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

    def __on_add_bl_button_cb(self, widget):
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK,
                                   None)
        def responseToDialog(entry, dialog, response):
            dialog.response(response)
            
        dialog.set_markup(_('Introduce the nannycentral repository url'))
	options = gtk.ListStore (str)
	options.append (['URL_DE_LA_LISTA'])
        entry = gtk.ComboBoxEntry(options, column=0)
        entry.child.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Url:"), False, 5, 5)
        hbox.pack_end(entry)
        dialog.format_secondary_markup(_("It's something like http://www.nannycentral.info/blacklist/blacklist.json ..."))
        dialog.vbox.pack_end(hbox, True, True, 0)
        dialog.show_all()
        dialog.run()
        text = entry.child.get_text()
        dialog.destroy()

        if not text.startswith("http:/") :
            text = "http://" + text

        result = self.dbus_client.add_pkg_filter (text)

    def __on_del_bl_button_cb(self, widget):
        try:
            selection = self.packaged_blacklist_treeview.get_selection()
            model, iter = selection.get_selected()
            pkg_id = model.get_value(iter, 0)
        except:
            return

        d = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL)
        d.set_property("icon-name", "nanny")
        d.set_markup(_("<b>Are you sure you want to delete this blacklist?</b>"))
        d.format_secondary_markup(_("This action will remove all the user configuration linked to the blacklist."))
        response = d.run()
        if response == gtk.RESPONSE_OK:
            self.dbus_client.remove_pkg_filter (pkg_id)

        d.destroy()
    
    def __on_update_bl_button_cb(self, widget):
        try:
            selection = self.packaged_blacklist_treeview.get_selection()
            model, iter = selection.get_selected()
            pkg_id = model.get_value(iter, 0)
        except:
            return

        self.dbus_client.update_pkg_filter (pkg_id)
        widget.set_sensitive(False)

    def __on_browser_use_proxy_checkbutton_toggled (self, widget, data=None):
        self.proxies_enabled = self.browser_use_proxy_checkbutton.get_active()

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
