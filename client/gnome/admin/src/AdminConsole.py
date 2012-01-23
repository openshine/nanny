#!/usr/bin/env python

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
if os.name == "posix":
    import dbus
elif os.name == "nt":
    import win32api
    import win32con

import gtk
import pango
import gobject

import nanny.client.common
import nanny.client.gnome.admin

class AdminConsole(gobject.GObject):

    __metaclass__ = nanny.client.common.Singleton

    def __init__(self):
        try:
            self.dbus_client = nanny.client.common.DBusClient ()
        except:
            d = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK)
            d.set_property("icon-name", "nanny")
            d.set_markup("<b>%s</b>" % _("Nanny daemon is not started"))
            d.format_secondary_markup(_("To use the parental control, please start up the daemon."))
            d.run()
            d.destroy()
            raise Exception ('DBus not initialized')

        nanny.client.common.Utils.ui_magic (self,
                                    ui_file = os.path.join (nanny.client.gnome.admin.ui_files_dir, "nanny_admin_console.ui"),
                                    prefix = "nac")

        self.window.connect ('delete-event', self.__on_close_event)
        self.close_button.connect ('clicked', self.__on_close_event)
        self.help_button.connect ('clicked', self.__on_help_button_clicked)
        self.apply_button.connect ('clicked', self.__on_apply_button_clicked)
        self.unlock_button.connect('clicked', self.__on_unlock_button_clicked)

        self.session_hoursday_checkbutton.connect ('toggled', self.__on_session_hoursday_checkbutton_toggled)
        self.session_hoursday_spinbutton.connect ('value-changed', self.__on_session_hoursday_spinbutton_changed)
        self.session_force_logoff_checkbutton.connect ('toggled', self.__on_session_force_logoff_checkbutton_toggled)
        self.session_grant_time_button.connect ('clicked', self.__on_session_grant_time_button_clicked)
        self.session_extrahours_spinbutton.connect ('value-changed', self.__on_session_extrahours_spinbutton_changed)
        self.session_configure_chores_button.connect ('clicked', self.__on_session_configure_chores_button_clicked)
        self.session_use_chores_indicator = None
        self.session_max_contracted_chores = None
        
        self.browser_configure_proxy_button.connect ('clicked', self.__on_browser_configure_proxy_button_clicked)
        self.browser_hoursday_checkbutton.connect ('toggled', self.__on_browser_hoursday_checkbutton_toggled)
        self.browser_hoursday_spinbutton.connect ('value-changed', self.__on_browser_hoursday_spinbutton_changed)
        self.browser_grant_time_button.connect ('clicked', self.__on_browser_grant_time_button_clicked)
        self.browser_extrahours_spinbutton.connect ('value-changed', self.__on_browser_extrahours_spinbutton_changed)
        self.browser_use_proxy_indicator = None

        self.mail_hoursday_checkbutton.connect ('toggled', self.__on_mail_hoursday_checkbutton_toggled)
        self.mail_hoursday_spinbutton.connect ('value-changed', self.__on_mail_hoursday_spinbutton_changed)
        self.mail_grant_time_button.connect ('clicked', self.__on_mail_grant_time_button_clicked)
        self.mail_extrahours_spinbutton.connect ('value-changed', self.__on_mail_extrahours_spinbutton_changed)

        self.im_hoursday_checkbutton.connect ('toggled', self.__on_im_hoursday_checkbutton_toggled)
        self.im_hoursday_spinbutton.connect ('value-changed', self.__on_im_hoursday_spinbutton_changed)
        self.im_grant_time_button.connect ('clicked', self.__on_im_grant_time_button_clicked)
        self.im_extrahours_spinbutton.connect ('value-changed', self.__on_im_extrahours_spinbutton_changed)


        self.session_schedule_widget = nanny.client.gnome.admin.ScheduleCalendar()
        self.session_schedule_alignment.add (self.session_schedule_widget)
        self.session_schedule_alignment.show_all()
        self.browser_schedule_widget = nanny.client.gnome.admin.ScheduleCalendar()
        self.browser_schedule_alignment.add (self.browser_schedule_widget)
        self.browser_schedule_alignment.show_all()
        self.mail_schedule_widget = nanny.client.gnome.admin.ScheduleCalendar()
        self.mail_schedule_alignment.add (self.mail_schedule_widget)
        self.mail_schedule_alignment.show_all()
        self.im_schedule_widget = nanny.client.gnome.admin.ScheduleCalendar()
        self.im_schedule_alignment.add (self.im_schedule_widget)
        self.im_schedule_alignment.show_all()

        self.__config_changed = False
        self.__selected_user_id = None

        self.__create_users_treeview ()
        self.__load_users_treeview ()

        treeselection = self.users_treeview.get_selection()
        model = self.users_treeview.get_model ()
        iter = model.get_iter_first ()
        if iter != None:
            treeselection.select_path ('0')
        else:
            self.__on_users_treeview_selection_changed (None)

        # for updating available time
        gobject.timeout_add(1000, self.__session_timeout_cb)
        gobject.timeout_add(1000, self.__browser_timeout_cb)
        gobject.timeout_add(1000, self.__mail_timeout_cb)
        gobject.timeout_add(1000, self.__im_timeout_cb)

        self.window.resize (800, 460)
        self.window.set_position (gtk.WIN_POS_CENTER)
        self.window.show_all ()

        self.__lock_widgets()

    def __lock_widgets(self) :
        lock_status = self.dbus_client.is_unlocked()
        if lock_status == True :
            self.unlock_area.hide()
        else:
            self.unlock_area.show()

        self.apply_button.set_sensitive(lock_status)

        self.session_configure_chores_button.set_sensitive(lock_status)
        self.session_hoursday_checkbutton.set_sensitive(lock_status)
        self.session_extrahours_entry.set_sensitive(lock_status)
        if lock_status == True:
            self.session_hoursday_spinbutton.set_sensitive(self.session_hoursday_checkbutton.get_active())
            self.session_extrahours_spinbutton.set_sensitive(self.session_hoursday_checkbutton.get_active())
            self.session_force_logoff_checkbutton.set_sensitive(self.session_hoursday_checkbutton.get_active())
        else:
            self.session_hoursday_spinbutton.set_sensitive(lock_status)
            self.session_extrahours_spinbutton.set_sensitive(lock_status)
            self.session_force_logoff_checkbutton.set_sensitive(lock_status)

        self.browser_configure_proxy_button.set_sensitive(lock_status)
        self.browser_hoursday_checkbutton.set_sensitive(lock_status)
        self.browser_extrahours_entry.set_sensitive(lock_status)
        if lock_status == True:
            self.browser_hoursday_spinbutton.set_sensitive(self.browser_hoursday_checkbutton.get_active())
            self.browser_extrahours_spinbutton.set_sensitive(self.browser_hoursday_checkbutton.get_active())
        else:
            self.browser_hoursday_spinbutton.set_sensitive(lock_status)
            self.browser_extrahours_spinbutton.set_sensitive(lock_status)

        self.mail_hoursday_checkbutton.set_sensitive(lock_status)
        self.mail_hoursday_spinbutton.set_sensitive(lock_status)
        self.mail_extrahours_entry.set_sensitive(lock_status)
        if lock_status == True:
            self.mail_hoursday_spinbutton.set_sensitive(self.mail_hoursday_checkbutton.get_active())
            self.mail_extrahours_spinbutton.set_sensitive(self.mail_hoursday_checkbutton.get_active())
        else:
            self.mail_hoursday_spinbutton.set_sensitive(lock_status)
            self.mail_extrahours_spinbutton.set_sensitive(lock_status)

        self.im_hoursday_checkbutton.set_sensitive(lock_status)
        self.im_hoursday_spinbutton.set_sensitive(lock_status)
        self.im_extrahours_entry.set_sensitive(lock_status)
        if lock_status == True:
            self.im_hoursday_spinbutton.set_sensitive(self.im_hoursday_checkbutton.get_active())
            self.im_extrahours_spinbutton.set_sensitive(self.im_hoursday_checkbutton.get_active())
        else:
            self.im_hoursday_spinbutton.set_sensitive(lock_status)
            self.im_extrahours_spinbutton.set_sensitive(lock_status)

        self.session_schedule_widget.set_sensitive(lock_status)
        self.browser_schedule_widget.set_sensitive(lock_status)
        self.mail_schedule_widget.set_sensitive(lock_status)
        self.im_schedule_widget.set_sensitive(lock_status)

    def __create_users_treeview (self):
        # UID
        col = gtk.TreeViewColumn ('uid')
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', 0)
        col.set_visible (False)
        self.users_treeview.append_column(col)

        # FACE
        col = gtk.TreeViewColumn (_('Users'))
        cell = gtk.CellRendererPixbuf()
        col.pack_start (cell, False)
        col.add_attribute(cell, 'pixbuf', 1)

        # NAME
        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        col.pack_start (cell, True)
        col.add_attribute(cell, 'text', 2)

        col.set_visible (True)
        self.users_treeview.append_column(col)

        model = gtk.ListStore(gobject.TYPE_STRING,
                              gtk.gdk.Pixbuf,
                              gobject.TYPE_STRING)

        self.users_treeview.set_model (model)

    def __load_users_treeview (self):
        model = self.users_treeview.get_model ()
        treeselection = self.users_treeview.get_selection()
        for uid, name, user_name in self.dbus_client.list_users ():
            print "uid: %s, name: %s, user_name: %s" % (uid, name, user_name)
            if os.name == "posix" :
                face_file = '/home/%s/.face' % name
            elif os.name == "nt" :
                import glob
                all_users_path = os.environ["ALLUSERSPROFILE"]
                face_file = None
                for p in glob.glob(os.path.join(all_users_path, "*", "Microsoft", "User Account Pictures", "%s.bmp" % name)):
                    face_file = p
                    print face_file
                    break

                if face_file == None:
                    face_file = "/fake/path"

            if os.path.exists (face_file):
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(face_file, 50, 50)
            else:
                if os.name == "posix" :
                    icon_theme = gtk.icon_theme_get_default()
                    pixbuf = icon_theme.load_icon ('stock_person', 50, gtk.ICON_LOOKUP_USE_BUILTIN)
                elif os.name == "nt" :
                    pixbuf = None

            if len(user_name) > 0 :
                model.append ([uid, pixbuf, user_name])
            else:
                model.append ([uid, pixbuf, name])
        treeselection.set_mode (gtk.SELECTION_SINGLE)
        self.users_selection_change_cb_id = treeselection.connect ("changed", self.__on_users_treeview_selection_changed)

    def __load_config (self):
        # SESSION
        self.session_schedule_widget.set_block_data (self.dbus_client.get_blocks (self.__selected_user_id, 0))
        value = self.dbus_client.get_max_use_time (self.__selected_user_id, 0)
        if value > 0:
            self.session_hoursday_checkbutton.set_active (True)
        else:
            self.session_hoursday_checkbutton.set_active (False)
        if self.session_hoursday_checkbutton.get_active ():
            self.session_hoursday_spinbutton.set_sensitive (True)
            self.session_hoursday_spinbutton.set_value (value/60.0)
            self.session_force_logoff_checkbutton.set_sensitive (True)
            self.session_force_logoff_checkbutton.set_active (self.dbus_client.is_forced_to_close (self.__selected_user_id, 0))
        else:
            self.session_hoursday_spinbutton.set_sensitive (False)
            self.session_hoursday_spinbutton.set_value (0)
            self.session_force_logoff_checkbutton.set_active (False)
            self.session_force_logoff_checkbutton.set_sensitive (False)
        self.session_use_chores_indicator, self.session_max_contracted_chores = self.dbus_client.get_chore_settings (self.__selected_user_id)

        # BROWSER
        self.browser_schedule_widget.set_block_data (self.dbus_client.get_blocks (self.__selected_user_id, 1))
        value = self.dbus_client.get_max_use_time (self.__selected_user_id, 1)
        if value > 0:
            self.browser_hoursday_checkbutton.set_active (True)
        else:
            self.browser_hoursday_checkbutton.set_active (False)
        if self.browser_hoursday_checkbutton.get_active ():
            self.browser_hoursday_spinbutton.set_sensitive (True)
            self.browser_hoursday_spinbutton.set_value (value/60.0)
        else:
            self.browser_hoursday_spinbutton.set_sensitive (False)
            self.browser_hoursday_spinbutton.set_value (0)

        if self.__selected_user_id in self.dbus_client.list_WCF ():
            self.browser_use_proxy_indicator = True
        else:
            self.browser_use_proxy_indicator = False

        # MAIL
        self.mail_schedule_widget.set_block_data (self.dbus_client.get_blocks (self.__selected_user_id, 2))
        value = self.dbus_client.get_max_use_time (self.__selected_user_id, 2)
        if value > 0:
            self.mail_hoursday_checkbutton.set_active (True)
        else:
            self.mail_hoursday_checkbutton.set_active (False)
        if self.mail_hoursday_checkbutton.get_active ():
            self.mail_hoursday_spinbutton.set_sensitive (True)
            self.mail_hoursday_spinbutton.set_value (value/60.0)
        else:
            self.mail_hoursday_spinbutton.set_sensitive (False)
            self.mail_hoursday_spinbutton.set_value (0)

        # IM
        self.im_schedule_widget.set_block_data (self.dbus_client.get_blocks (self.__selected_user_id, 3))
        value = self.dbus_client.get_max_use_time (self.__selected_user_id, 3)
        if value > 0:
            self.im_hoursday_checkbutton.set_active (True)
        else:
            self.im_hoursday_checkbutton.set_active (False)
        if self.im_hoursday_checkbutton.get_active ():
            self.im_hoursday_spinbutton.set_sensitive (True)
            self.im_hoursday_spinbutton.set_value (value/60.0)
        else:
            self.im_hoursday_spinbutton.set_sensitive (False)
            self.im_hoursday_spinbutton.set_value (0)

        self.__config_changed = False

    def __on_browser_configure_proxy_button_clicked (self, widget, data=None):
        configure_proxy_dialog = nanny.client.gnome.admin.ConfigureProxyDialog(self.__selected_user_id, self.browser_use_proxy_indicator)
        configure_proxy_dialog.set_transient_for(self.window)
        ret = configure_proxy_dialog.run()
        if ret != self.browser_use_proxy_indicator:
            self.browser_use_proxy_indicator = ret
            self.__config_changed = True
            
        configure_proxy_dialog.destroy()

    def __on_session_configure_chores_button_clicked (self, widget, data=None):
        configure_chores_dialog = nanny.client.gnome.admin.ConfigureChoresDialog(self.__selected_user_id, self.session_use_chores_indicator, self.session_max_contracted_chores)
        configure_chores_dialog.set_transient_for(self.window)
        ret = configure_chores_dialog.run()
        if ret[0] != self.session_use_chores_indicator or ret[1] != self.session_max_contracted_chores:
            self.session_use_chores_indicator = ret[0]
            self.session_max_contracted_chores = ret[1]
            self.__config_changed = True
        configure_chores_dialog.destroy()

    def __on_apply_button_clicked (self, widget, data=None):
        # SESSION
        schedule_data = self.session_schedule_widget.get_block_data()
        self.dbus_client.set_blocks (self.__selected_user_id, 0, schedule_data)
        self.dbus_client.set_chore_settings (self.__selected_user_id, self.session_use_chores_indicator, self.session_max_contracted_chores)
        if self.session_hoursday_checkbutton.get_active ():
            value = self.session_hoursday_spinbutton.get_value()
            self.dbus_client.set_max_use_time(self.__selected_user_id, 0, value*60.0)
            self.dbus_client.set_forced_to_close (self.__selected_user_id, 0, self.session_force_logoff_checkbutton.get_active ())
        else:
            self.dbus_client.set_max_use_time(self.__selected_user_id, 0, 0)

        # BROWSER
        schedule_data = self.browser_schedule_widget.get_block_data()
        self.dbus_client.set_blocks (self.__selected_user_id, 1, schedule_data)
        if self.browser_use_proxy_indicator:
            self.dbus_client.set_active_WCF (self.__selected_user_id, True)
        else:
            self.dbus_client.set_active_WCF (self.__selected_user_id, False)
        if self.browser_hoursday_checkbutton.get_active ():
            value = self.browser_hoursday_spinbutton.get_value()
            self.dbus_client.set_max_use_time(self.__selected_user_id, 1, value*60.0)
        else:
            self.dbus_client.set_max_use_time(self.__selected_user_id, 1, 0)

        # MAIL
        schedule_data = self.mail_schedule_widget.get_block_data()
        self.dbus_client.set_blocks (self.__selected_user_id, 2, schedule_data)
        if self.mail_hoursday_checkbutton.get_active ():
            value = self.mail_hoursday_spinbutton.get_value()
            self.dbus_client.set_max_use_time(self.__selected_user_id, 2, value*60.0)
        else:
            self.dbus_client.set_max_use_time(self.__selected_user_id, 2, 0)

        # IM
        schedule_data = self.im_schedule_widget.get_block_data()
        self.dbus_client.set_blocks (self.__selected_user_id, 3, schedule_data)
        if self.im_hoursday_checkbutton.get_active ():
            value = self.im_hoursday_spinbutton.get_value()
            self.dbus_client.set_max_use_time(self.__selected_user_id, 3, value*60.0)
        else:
            self.dbus_client.set_max_use_time(self.__selected_user_id, 3, 0)

        self.__config_changed = False
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
                                   _("User's configuration has been saved") )
        dialog.set_property("icon-name", "nanny")
        dialog.set_transient_for(self.window)
        dialog.set_default_response(gtk.RESPONSE_CLOSE)
        dialog.run()
        dialog.destroy()


    def __on_users_treeview_selection_changed (self, widget):
        if not self.ignore_changes_made():
            return
        
        selection = self.users_treeview.get_selection()

        selected_rows =  selection.count_selected_rows()
        new_state = selected_rows > 0
        self.apply_button.set_sensitive(new_state)
        self.main_notebook.set_sensitive(new_state)

        if selected_rows > 0:
            model, itera = selection.get_selected ()
            self.__selected_user_id = model.get_value (itera, 0)

            if self.dbus_client.is_unlocked():    
                self.__load_config ()
            
            self.window.set_title (_('Nanny Admin Console - %s') % self.users_treeview.get_model().get_value (itera, 2))
        else:
            self.__selected_user_id = None
            self.window.set_title (_('Nanny Admin Console'))

        self.__lock_widgets()

    def __on_session_hoursday_spinbutton_changed (self, widget, data=None):
        self.__config_changed = True
    def __on_session_hoursday_checkbutton_toggled (self, widget, data=None):
        self.__config_changed = True
        if self.session_hoursday_checkbutton.get_active():
            self.session_hoursday_spinbutton.set_sensitive (True)
            self.session_extrahours_spinbutton.set_sensitive (True)
            self.session_extrahours_entry.set_sensitive (True)
            self.session_force_logoff_checkbutton.set_sensitive(True)
        else:
            self.session_hoursday_spinbutton.set_sensitive (False)
            self.session_grant_time_button.set_sensitive (False)
            self.session_extrahours_spinbutton.set_sensitive (False)
            self.session_extrahours_entry.set_sensitive (False)
            self.session_force_logoff_checkbutton.set_sensitive(False)
    def __on_session_force_logoff_checkbutton_toggled (self, widget, data=None):
        self.__config_changed = True

    def __on_session_extrahours_spinbutton_changed (self, widget, data=None):
        if self.session_extrahours_spinbutton.get_value() != 0:
            self.session_grant_time_button.set_sensitive (True)
        else:
            self.session_grant_time_button.set_sensitive (False)
    def __on_session_grant_time_button_clicked (self, widget, data=None):
        value = self.session_extrahours_spinbutton.get_value()
        self.dbus_client.add_use_time(self.__selected_user_id, 0, value*60.0)
        
    def __on_browser_hoursday_spinbutton_changed (self, widget, data=None):
        self.__config_changed = True
    def __on_browser_hoursday_checkbutton_toggled (self, widget, data=None):
        self.__config_changed = True
        if self.browser_hoursday_checkbutton.get_active():
            self.browser_hoursday_spinbutton.set_sensitive (True)
            self.browser_extrahours_spinbutton.set_sensitive (True)
            self.browser_extrahours_entry.set_sensitive (True)
        else:
            self.browser_hoursday_spinbutton.set_sensitive (False)
            self.browser_grant_time_button.set_sensitive (False)
            self.browser_extrahours_spinbutton.set_sensitive (False)
            self.browser_extrahours_entry.set_sensitive (False)

    def __on_browser_extrahours_spinbutton_changed (self, widget, data=None):
        if self.browser_extrahours_spinbutton.get_value() != 0:
            self.browser_grant_time_button.set_sensitive (True)
        else:
            self.browser_grant_time_button.set_sensitive (False)
    def __on_browser_grant_time_button_clicked (self, widget, data=None):
        value = self.browser_extrahours_spinbutton.get_value()
        self.dbus_client.add_use_time(self.__selected_user_id, 1, value*60.0)

    def __on_mail_hoursday_spinbutton_changed (self, widget, data=None):
        self.__config_changed = True
    def __on_mail_hoursday_checkbutton_toggled (self, widget, data=None):
        self.__config_changed = True
        if self.mail_hoursday_checkbutton.get_active():
            self.mail_hoursday_spinbutton.set_sensitive (True)
            self.mail_extrahours_spinbutton.set_sensitive (True)
            self.mail_extrahours_entry.set_sensitive (True)
        else:
            self.mail_hoursday_spinbutton.set_sensitive (False)
            self.mail_grant_time_button.set_sensitive (False)
            self.mail_extrahours_spinbutton.set_sensitive (False)
            self.mail_extrahours_entry.set_sensitive (False)

    def __on_mail_extrahours_spinbutton_changed (self, widget, data=None):
        if self.mail_extrahours_spinbutton.get_value() != 0:
            self.mail_grant_time_button.set_sensitive (True)
        else:
            self.mail_grant_time_button.set_sensitive (False)
    def __on_mail_grant_time_button_clicked (self, widget, data=None):
        value = self.mail_extrahours_spinbutton.get_value()
        self.dbus_client.add_use_time(self.__selected_user_id, 2, value*60.0)

    def __on_im_hoursday_spinbutton_changed (self, widget, data=None):
        self.__config_changed = True
    def __on_im_hoursday_checkbutton_toggled (self, widget, data=None):
        self.__config_changed = True
        if self.im_hoursday_checkbutton.get_active():
            self.im_hoursday_spinbutton.set_sensitive (True)
            self.im_extrahours_spinbutton.set_sensitive (True)
            self.im_extrahours_entry.set_sensitive (True)
        else:
            self.im_hoursday_spinbutton.set_sensitive (False)
            self.im_grant_time_button.set_sensitive (False)
            self.im_extrahours_spinbutton.set_sensitive (False)
            self.im_extrahours_entry.set_sensitive (False)

    def __on_im_extrahours_spinbutton_changed (self, widget, data=None):
        if self.im_extrahours_spinbutton.get_value() != 0:
            self.im_grant_time_button.set_sensitive (True)
        else:
            self.im_grant_time_button.set_sensitive (False)
    def __on_im_grant_time_button_clicked (self, widget, data=None):
        value = self.im_extrahours_spinbutton.get_value()
        self.dbus_client.add_use_time(self.__selected_user_id, 3, value*60.0)

    def __on_help_button_clicked (self, widget, data=None):
        if os.name == "posix":
            try:
                gtk.show_uri(None , "ghelp:nanny", gtk.get_current_event_time())
            except:
                os.system("yelp ghelp:nanny")
        elif os.name == "nt":
            win32api.ShellExecute(None, "open",
                                  "http://library.gnome.org/users/nanny/stable/",
                                  None, None, win32con.SW_SHOWNORMAL)

    def __on_unlock_button_clicked (self, widget, data=None):
        self.dbus_client.unlock()
        self.__on_users_treeview_selection_changed(None)
        self.__lock_widgets()

    def __on_close_event (self, widget, data=None):
        if not self.ignore_changes_made():
            return True
        gtk.main_quit()

    def __session_timeout_cb(self):
        if self.__selected_user_id is not None:
            if self.dbus_client.is_unlocked():
                value = self.dbus_client.get_use_time (self.__selected_user_id, 0)
                if value >= 0:
                    self.session_extrahours_entry.set_text("{0:.1f}".format(value/60.0))
                else:
                    self.session_extrahours_entry.set_text("{0:.1f}".format(0))
            gobject.timeout_add(1000, self.__session_timeout_cb)

    def __browser_timeout_cb(self):
        if self.__selected_user_id is not None:
            if self.dbus_client.is_unlocked():
                value = self.dbus_client.get_use_time (self.__selected_user_id, 1)
                if value >= 0:
                    self.browser_extrahours_entry.set_text("{0:.1f}".format(value/60.0))
                else:
                    self.browser_extrahours_entry.set_text("{0:.1f}".format(0))
            gobject.timeout_add(1000, self.__browser_timeout_cb)

    def __mail_timeout_cb(self):
        if self.__selected_user_id is not None:
            if self.dbus_client.is_unlocked():
                value = self.dbus_client.get_use_time (self.__selected_user_id, 2)
                if value >= 0:
                    self.mail_extrahours_entry.set_text("{0:.1f}".format(value/60.0))
                else:
                    self.mail_extrahours_entry.set_text("{0:.1f}".format(0))
            gobject.timeout_add(1000, self.__mail_timeout_cb)

    def __im_timeout_cb(self):
        if self.__selected_user_id is not None:
            if self.dbus_client.is_unlocked():
                value = self.dbus_client.get_use_time (self.__selected_user_id, 3)
                if value >= 0:
                    self.im_extrahours_entry.set_text("{0:.1f}".format(value/60.0))
                else:
                    self.im_extrahours_entry.set_text("{0:.1f}".format(0))
            gobject.timeout_add(1000, self.__im_timeout_cb)
                
    def ignore_changes_made (self):
        """Asks confirmation if user doesn't want to save changes. No changes made is equal to ignoring changes."""
        if self.__config_changed:
            dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO)
            dialog.set_property("icon-name", "nanny")
            dialog.set_markup ("<b>%s</b>" % _('You have made changes'))
            dialog.format_secondary_markup (_("If you don't press the 'Apply' button, your changes will be lost.\nAre you sure?") )
            dialog.set_default_response(gtk.RESPONSE_YES)
            ret = dialog.run()
            if ret == gtk.RESPONSE_NO:
                dialog.destroy()

                selection = self.users_treeview.get_selection()
                selection.disconnect (self.users_selection_change_cb_id)
                model = self.users_treeview.get_model ()
                for row in model:
                    if row[0] == self.__selected_user_id:
                        selection.select_iter (row.iter)
                        break
                self.users_selection_change_cb_id = selection.connect ('changed', self.__on_users_treeview_selection_changed)
                return False
            else:
                dialog.destroy()
                return True
            
        return True
        
