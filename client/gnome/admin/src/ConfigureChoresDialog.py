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

import datetime
import time

import nanny

class ConfigureChoresDialog (gtk.Dialog):
    def __init__ (self, selected_user_id, chores_enabled, max_chores_to_contract):
        gtk.Dialog.__init__ (self, title=_("Chores & Rewards Configuration"), buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.chores_enabled = chores_enabled
        self.max_chores_to_contract = max_chores_to_contract

        nanny.client.common.Utils.ui_magic (self,
                ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nac_chores_dialog.ui"),
                prefix = "chd")

        self.set_property("icon-name", "nanny")
        self.dbus_client = nanny.client.common.DBusClient ()
        self.__selected_user_id = selected_user_id

        self.main_vbox.unparent()
        self.get_content_area().add (self.main_vbox)

        self.session_use_chores_checkbutton.set_active(self.chores_enabled)
        self.session_use_chores_checkbutton.connect('toggled', self.__on_session_use_chores_checkbutton_toggled)
        
        self.session_max_chores_to_contract_spinbutton.set_value(self.max_chores_to_contract)
        self.session_max_chores_to_contract_spinbutton.connect('value-changed', self.__on_session_max_chores_to_contract_spinbutton_changed)

        self.finished_chores_remove_button.connect ('clicked', self.__on_finished_chores_remove_button_clicked)
        self.chore_progress_cancel_button.connect ('clicked', self.__on_chore_progress_cancel_button_clicked)
        self.chore_progress_done_button.connect ('clicked', self.__on_chore_progress_done_button_clicked)

        self.add_lst_button.connect("clicked", self.__on_add_lst_button_cb)
        self.del_lst_button.connect("clicked", self.__on_del_lst_button_cb)
        self.edit_lst_button.connect("clicked", self.__on_edit_lst_button_cb)

        self.assign_button.connect("clicked", self.__on_assign_button_cb)
        
        self.__init_chore_assign_treeview (self.chore_assign_treeview)
        self.__init_enabled_chores_treeview (self.enabled_chores_treeview)
        self.__init_chore_progress_treeview (self.chore_progress_treeview)
        self.__init_finished_chores_treeview (self.finished_chores_treeview)
        self.__fill_treeviews ()

        selection = self.chore_assign_treeview.get_selection()
        selection.connect ('changed', self.__on_chore_assign_selection_changed)
        self.chore_assign_treeview.connect ('focus-in-event', self.__on_chore_assign_focus_received)
        self.__on_chore_assign_selection_changed (selection)

        selection = self.enabled_chores_treeview.get_selection()
        selection.connect ('changed', self.__on_enabled_chores_selection_changed)
        self.enabled_chores_treeview.connect ('focus-in-event', self.__on_enabled_chores_focus_received)
        self.__on_enabled_chores_selection_changed (selection)

        selection = self.chore_progress_treeview.get_selection()
        selection.connect ('changed', self.__on_chore_progress_selection_changed)
        self.__on_chore_progress_selection_changed (selection)

        selection = self.finished_chores_treeview.get_selection()
        selection.connect ('changed', self.__on_finished_chores_selection_changed)
        self.__on_finished_chores_selection_changed (selection)

        self.fw_image = gtk.Image()
        self.bw_image = gtk.Image()
        self.fw_image.set_from_stock (gtk.STOCK_GO_FORWARD, gtk.ICON_SIZE_BUTTON)
        self.bw_image.set_from_stock (gtk.STOCK_GO_BACK, gtk.ICON_SIZE_BUTTON)

        self.resize (700, 460)

        self.show_all ()

    def run(self):
        super(ConfigureChoresDialog, self).run()
        
        return [self.chores_enabled, self.max_chores_to_contract]

    def __init_chore_assign_treeview (self, treeview):
        base_id = 0
        for field in ["id", "title", "description", "reward"]:
            col = gtk.TreeViewColumn(field)
            treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            if field in ("id", "description"):
                col.set_visible (False)
            else:
                col.set_visible (True)
            if field == "title":
                col.set_expand(True)
                col.set_resizable(True)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            if field == "description":
                col.set_expand(True)
                col.set_resizable(True)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            if field == "reward":
                col.set_alignment(1.0)
                col.set_min_width(50)
                col.set_resizable(True)
                cell.set_property("alignment", pango.ALIGN_RIGHT)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            base_id = base_id + 1

        store = gtk.ListStore (gobject.TYPE_INT,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)

    def __init_enabled_chores_treeview (self, treeview):
        base_id = 0
        for field in ["id", "title", "description"]:
            col = gtk.TreeViewColumn(field)
            treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            if field in ("id", "description"):
                col.set_visible (False)
            else:
                col.set_visible (True)
            if field == "title":
                col.set_expand(True)
                col.set_resizable(True)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            base_id = base_id + 1

        store = gtk.ListStore (gobject.TYPE_INT,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)

    def __init_chore_progress_treeview (self, treeview):
        base_id = 0
        for field in ["id", "title", "description", "contracted"]:
            col = gtk.TreeViewColumn(field)
            treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            if field in ("id", "description"):
                col.set_visible (False)
            else:
                col.set_visible (True)
            if field == "title":
                col.set_expand(True)
                col.set_resizable(True)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            if field == "description":
                col.set_expand(True)
                col.set_resizable(True)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            if field == "contracted":
                col.set_alignment(1.0)
                col.set_min_width(100)
                col.set_resizable(True)
                cell.set_property("alignment", pango.ALIGN_RIGHT)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            base_id = base_id + 1

        store = gtk.ListStore (gobject.TYPE_INT,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)
        
    def __init_finished_chores_treeview (self, treeview):
        base_id = 0
        for field in ["id", "title", "description", "contracted", "finished"]:
            col = gtk.TreeViewColumn(field)
            treeview.append_column(col)
            cell = gtk.CellRendererText()
            cell.set_property("ellipsize", pango.ELLIPSIZE_END)
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', base_id)
            if field in ("id", "description"):
                col.set_visible (False)
            else:
                col.set_visible (True)
            if field == "title":
                col.set_expand(True)
                col.set_resizable(True)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            if field == "description":
                col.set_expand(True)
                col.set_resizable(True)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            if field in ("contracted", "finished"):
                col.set_alignment(1.0)
                col.set_min_width(100)
                col.set_resizable(True)
                cell.set_property("alignment", pango.ALIGN_RIGHT)
                col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            base_id = base_id + 1

        store = gtk.ListStore (gobject.TYPE_INT,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        treeview.set_model (store)
        

    def tooltip_callback(self, widget, x, y, keyboard_mode, tooltip, tooltip_column):
        if widget.get_path_at_pos(x,y) is None:
            return False
        m = widget.get_model()
        i = m.get_iter_from_string(str(widget.get_path_at_pos(x,y)[0][0]))
        v = m.get_value(i, tooltip_column)
        if len(v) > 0:
            tooltip.set_text(v)
            return True
        else:
            return False

    def __fill_treeviews (self, skip_assign_tree=False):
        if not skip_assign_tree:
            chore_assign_model = self.chore_assign_treeview.get_model()
            chore_assign_model.clear()
            self.chore_assign_treeview.set_property("has-tooltip", True)
            self.chore_assign_treeview.connect("query-tooltip", self.tooltip_callback, 2)

            chore_descriptions = self.dbus_client.list_chore_descriptions ()
            for desc_id, title, description, reward in chore_descriptions:
                row_path = chore_assign_model.append ((desc_id, title, description, "{0:.1f}".format(int(reward)/60.0)))

        enabled_chores_model = self.enabled_chores_treeview.get_model()
        enabled_chores_model.clear()
        self.enabled_chores_treeview.set_property("has-tooltip", True)
        self.enabled_chores_treeview.connect("query-tooltip", self.tooltip_callback, 2)

        chores = self.dbus_client.list_chores (self.__selected_user_id, available=True)
        for assign_id, chore_id, uid, reward, contracted, finished, title, description in chores:
            row_path = enabled_chores_model.append ((assign_id, title, description))

        chore_progress_model = self.chore_progress_treeview.get_model()
        chore_progress_model.clear()
        self.chore_progress_treeview.set_property("has-tooltip", True)
        self.chore_progress_treeview.connect("query-tooltip", self.tooltip_callback, 2)

        chores = self.dbus_client.list_chores (self.__selected_user_id, contracted=True)
        for assign_id, chore_id, uid, reward, contracted, finished, title, description in chores:
            row_path = chore_progress_model.append ((assign_id, title, description, datetime.datetime.fromtimestamp(int(contracted)).strftime("%x")))

        finished_chores_model = self.finished_chores_treeview.get_model()
        finished_chores_model.clear()
        self.finished_chores_treeview.set_property("has-tooltip", True)
        self.finished_chores_treeview.connect("query-tooltip", self.tooltip_callback, 2)

        chores = self.dbus_client.list_chores (self.__selected_user_id, finished=True)
        for assign_id, chore_id, uid, reward, contracted, finished, title, description in chores:
            row_path = finished_chores_model.append ((assign_id, title, description, datetime.datetime.fromtimestamp(int(contracted)).strftime("%x"), datetime.datetime.fromtimestamp(int(contracted)).strftime("%x")))

    def __on_chore_progress_done_button_clicked (self, widget, data=None):
        try:
            selection = self.chore_progress_treeview.get_selection()
            model, iter = selection.get_selected()
            desc_id = model.get_value(iter, 0)
        except:
            return
            
        self.dbus_client.finish_chore (desc_id, int(time.time()))
            
        self.__fill_treeviews ()

    def __on_finished_chores_remove_button_clicked (self, widget, data=None):
        try:
            selection = self.finished_chores_treeview.get_selection()
            model, iter = selection.get_selected()
            desc_id = model.get_value(iter, 0)
        except:
            return
            
        self.dbus_client.remove_chore (desc_id, self.__on_remove_reply, self.__on_remove_error)
            
        self.__fill_treeviews ()
        

    def __on_chore_progress_cancel_button_clicked (self, widget, data=None):
        try:
            selection = self.chore_progress_treeview.get_selection()
            model, iter = selection.get_selected()
            desc_id = model.get_value(iter, 0)
        except:
            return
            
        self.dbus_client.remove_chore (desc_id, self.__on_remove_reply, self.__on_remove_error)
            
        self.__fill_treeviews ()
        

    def __on_chore_assign_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.edit_lst_button.set_sensitive (True)
            self.del_lst_button.set_sensitive (True)
            self.assign_button.set_sensitive (True)
        else:
            self.edit_lst_button.set_sensitive (False)
            self.del_lst_button.set_sensitive (False)

    def __on_enabled_chores_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.edit_lst_button.set_sensitive (False)
            self.del_lst_button.set_sensitive (False)
            self.assign_button.set_sensitive (True)
        else:
            self.edit_lst_button.set_sensitive (False)
            self.del_lst_button.set_sensitive (False)
        
    def __on_chore_assign_focus_received (self, widget, direction, data=None):
            self.assign_button.set_sensitive (True)
            self.assign_button.set_image(self.fw_image)
    
    def __on_enabled_chores_focus_received (self, widget, direction, data=None):
            self.assign_button.set_sensitive (True)
            self.assign_button.set_image(self.bw_image)

    def __on_chore_progress_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.chore_progress_cancel_button.set_sensitive (True)
            self.chore_progress_done_button.set_sensitive (True)
        else:
            self.chore_progress_cancel_button.set_sensitive (False)
            self.chore_progress_done_button.set_sensitive (False)
        

    def __on_finished_chores_selection_changed (self, selection, data=None):
        if selection.count_selected_rows () > 0:
            self.finished_chores_remove_button.set_sensitive (True)
        else:
            self.finished_chores_remove_button.set_sensitive (False)
        
    def __on_entry_dialog_essential_values_changed(self, widget, ok_button, title_entry, reward_spinbutton):
        title = title_entry.get_text().strip()
        reward = reward_spinbutton.get_value()
        
        if title == "": # or reward == 0.0:
            ok_button.set_sensitive (False)
        else:
            ok_button.set_sensitive (True)

    def __on_add_lst_button_cb(self, widget):
        xml = self.__load_dialog ()
        self.chore_edit_dialog = xml.get_object ('chd_edit_dialog')
        self.chore_edit_dialog.set_title(_("Add chore description"))
        self.chore_edit_dialog.set_transient_for(self)
        
        information_label = xml.get_object ("chd_information_label")
        ok_button = xml.get_object ('chd_ok_button')
        title_entry = xml.get_object ('chd_title_entry')
        description_entry = xml.get_object ('chd_description_entry')
        reward_spinbutton = xml.get_object ('chd_reward_spinbutton')

        title_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, title_entry, reward_spinbutton)
        reward_spinbutton.connect ('value-changed', self.__on_entry_dialog_essential_values_changed, ok_button, title_entry, reward_spinbutton)

        ret = self.chore_edit_dialog.run()
        if ret == 2:
            title = title_entry.get_text().strip()
            description = description_entry.get_text().strip()
            reward = reward_spinbutton.get_value()
            self.dbus_client.add_chore_description (title, description, int(reward*60.0))
            self.__fill_treeviews ()
            
        self.chore_edit_dialog.destroy()
                
    def __on_edit_lst_button_cb(self, widget):
        try:
            selection = self.chore_assign_treeview.get_selection()
            model, iter = selection.get_selected()
            desc_id = model.get_value(iter, 0)
        except:
            return

        xml = self.__load_dialog ()
        self.chore_edit_dialog = xml.get_object ('chd_edit_dialog')
        self.chore_edit_dialog.set_title(_("Edit chore description"))
        self.chore_edit_dialog.set_transient_for(self)
        
        information_label = xml.get_object ("chd_information_label")
        ok_button = xml.get_object ('chd_ok_button')
        title_entry = xml.get_object ('chd_title_entry')
        description_entry = xml.get_object ('chd_description_entry')
        reward_spinbutton = xml.get_object ('chd_reward_spinbutton')

        chore_descriptions = self.dbus_client.list_chore_descriptions (int(desc_id))
        for desc_id, title, description, reward in chore_descriptions:
            title_entry.set_text(title)
            description = description_entry.set_text(description)
            reward = reward_spinbutton.set_value(reward/60.0)
            break

        title_entry.connect ('changed', self.__on_entry_dialog_essential_values_changed, ok_button, title_entry, reward_spinbutton)
        reward_spinbutton.connect ('value-changed', self.__on_entry_dialog_essential_values_changed, ok_button, title_entry, reward_spinbutton)

        ret = self.chore_edit_dialog.run()
        if ret == 2:
            title = title_entry.get_text().strip()
            description = description_entry.get_text().strip()
            reward = reward_spinbutton.get_value()
            self.dbus_client.update_chore_description (int(desc_id), title, description, int(reward*60.0))
            self.__fill_treeviews ()
            
        self.chore_edit_dialog.destroy()
        
    def __on_del_lst_button_cb(self, widget):
        try:
            selection = self.chore_assign_treeview.get_selection()
            model, iter = selection.get_selected()
            desc_id = model.get_value(iter, 0)
        except:
            return

        d = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL)
        d.set_property("icon-name", "nanny")
        d.set_markup(_("<b>Are you sure you want to delete this chore description entry?</b>"))
        d.format_secondary_markup(_("This action will remove all the user chores linked to the description."))
        response = d.run()
        if response == gtk.RESPONSE_OK:
            self.dbus_client.remove_chore_description (desc_id, self.__on_remove_reply, self.__on_remove_error)

        d.destroy()

    def __on_assign_button_cb(self, widget):
        desc_id = None
        
        if self.enabled_chores_treeview.has_focus():
            try:
                selection = self.enabled_chores_treeview.get_selection()
                model, iter = selection.get_selected()
                desc_id = model.get_value(iter, 0)
                
                self.dbus_client.remove_chore (desc_id, self.__on_remove_reply, self.__on_remove_error)

            except:
                return
            
            
        elif self.chore_assign_treeview.has_focus():
            try:
                selection = self.chore_assign_treeview.get_selection()
                model, iter = selection.get_selected()
                desc_id = model.get_value(iter, 0)
                
                self.dbus_client.add_chore (desc_id, self.__selected_user_id)

                self.__fill_treeviews (skip_assign_tree=True)
                self.chore_assign_treeview.grab_focus()
            except:
                return



    def __on_session_use_chores_checkbutton_toggled (self, widget, data=None):
        self.chores_enabled = self.session_use_chores_checkbutton.get_active()

    def __on_session_max_chores_to_contract_spinbutton_changed (self, widget, data=None):
        self.max_chores_to_contract = self.session_max_chores_to_contract_spinbutton.get_value()
    
    def __load_dialog (self):
        ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nac_chores_edit_dialog.ui")
        xml = gtk.Builder ()
        xml.add_from_file (ui_file)

        return xml
        
    def __on_remove_reply (self, value):

        if value:
            self.__fill_treeviews ()
        else:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dlg.set_property("icon-name", "nanny")
            dlg.set_markup("<b>%s</b>" % _("Error while deleting the chore entry"))
            dlg.format_secondary_markup(_("Some error has occured while deleting the chore entry.\nPlease try again."))
            dlg.run()
            dlg.destroy()

    def __on_remove_error (self, exception):

        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dlg.set_property("icon-name", "nanny")
        dlg.set_markup("<b>%s</b>" % _("Error while deleting the chore entry"))
        dlg.format_secondary_markup(_("Some error has occured while deleting the chore entry.\nPlease try again."))
        dlg.run()
        dlg.destroy()


