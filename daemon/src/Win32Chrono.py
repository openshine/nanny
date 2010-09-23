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

import gobject
import os

import pickle
import datetime

(
SESSION_APPID,
WEB_APPID,
MAIL_APPID,
IM_APPID) = range(4)


class Win32Chrono(gobject.GObject) :
    '''
    This class handles the use time of all application categories that
    Gnome Nanny controls.

    Application list is generated from files in:
        /var/lib/nanny/applists/
    There is one file per category and each line in the file is an
    application name.

    Max time of use per day of the categories is set in Gnome Nannys
    Admin Console.
    '''
    def __init__(self, quarterback): 
        '''Init function for NannyChrono class.'''
        gobject.GObject.__init__(self)
        self.quarterback = quarterback

        file_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for x in range(6):
            file_dir = os.path.dirname(file_dir)
        root_path = file_dir
        self.apps_list_path = os.path.join(root_path, "etc", "nanny", "applists")

        self.day = datetime.date.today().day
        self.categories = ['session', 'browser', 'email', 'im']

        self.quarterback.connect('block-status', self.__update_cb)

    def __update_cb(self, quarterback, block_status, user_id, app_id, next_change, available_time):
        '''Callback that updates the used times of the categories.'''
        if block_status == False:
            app_list = self.__get_application_list(self.categories)
            proclist = self.quarterback.win32top.proclist(int(user_id))
            
            if app_id == SESSION_APPID :
                try:
                    if self.quarterback.win32top.get_current_user_session() == int(user_id) :
                        self.quarterback.subtract_time(user_id, app_id)
                        return
                except:
                    print "Crash Chrono __update_cb"
            else:
                category = self.categories[app_id]
                found = False
                for proc in proclist:
                    if len(self.quarterback.win32top.proc_args(proc)) > 0:
                        process = self.quarterback.win32top.proc_args(proc)
                        if self.is_a_controlled_app(process, category, app_list):
                            self.quarterback.subtract_time(user_id, app_id)
                            return

    def is_a_controlled_app(self, process, category, app_list):
        found = False

        for app in app_list:
            if app[0] == category:
                if process == app[1]:
                    found = True
                    break

        return found

    def __get_application_list(self, categories):
        '''Generate the application list from the app files.

        Format:
            app_list = [['browser', 'firefox'],
                        ['email', 'thunderbird']]
        '''

        app_list = []
        for category in categories:
            file_path = os.path.join(self.apps_list_path, category + ".w32")
            if os.path.exists(file_path):
                file = open(file_path, 'rb')
                for line in file:
                    if len(line) > 1:
                        app_list.append([category, line[:-1]])

        return app_list


gobject.type_register(Win32Chrono)
