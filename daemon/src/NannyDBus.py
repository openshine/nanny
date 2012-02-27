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

import gobject
import os
import dbus
import dbus.service
import dbus.mainloop.glib
import gtop

class PermissionDeniedByPolicy(dbus.DBusException):
    _dbus_error_name = 'org.gnome.nanny.PermissionDeniedByPolicy'

class NannyDBus(dbus.service.Object):
    def __init__ (self, quarterback):
        
        self.quarterback = quarterback
        
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        dbus.service.Object.__init__(self,
                                     dbus.service.BusName("org.gnome.Nanny", dbus.SystemBus()),
                                     "/org/gnome/Nanny")

        self.quarterback.connect('block-status', self.__UserNotification_cb)
        self.quarterback.connect('update-users-info', self.__UpdateUsersInfo_cb)
        
        self.dbus_info = None
        self.polkit = None
        self.auth_pid_cache = []

        gobject.timeout_add(1000, self.__polling_cb)

    def __polling_cb(self):
        self.auth_pid_cache = list(set(gtop.proclist()).intersection(set(self.auth_pid_cache)))
        return True

    # Taken from Jockey 0.5.8.
    def _check_polkit_privilege(self, sender, conn, privilege):
        '''Verify that sender has a given PolicyKit privilege.

        sender is the sender's (private) D-BUS name, such as ":1:42"
        (sender_keyword in @dbus.service.methods). conn is
        the dbus.Connection object (connection_keyword in
        @dbus.service.methods). privilege is the PolicyKit privilege string.

        This method returns if the caller is privileged, and otherwise throws a
        PermissionDeniedByPolicy exception.
        '''
        if sender is None and conn is None:
            # called locally, not through D-BUS
            return

        # get peer PID
        if self.dbus_info is None:
            self.dbus_info = dbus.Interface(conn.get_object('org.freedesktop.DBus',
                '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        pid = self.dbus_info.GetConnectionUnixProcessID(sender)

        if int(pid) in self.auth_pid_cache :
            return

        # query PolicyKit
        if self.polkit is None:
            self.polkit = dbus.Interface(dbus.SystemBus().get_object(
                'org.freedesktop.PolicyKit1',
                '/org/freedesktop/PolicyKit1/Authority', False),
                'org.freedesktop.PolicyKit1.Authority')
        try:
            # we don't need is_challenge return here, since we call with AllowUserInteraction
            (is_auth, _, details) = self.polkit.CheckAuthorization(
                    ('unix-process', {'pid': dbus.UInt32(pid, variant_level=1),
                        'start-time': dbus.UInt64(0, variant_level=1)}),
                    privilege, {'': ''}, dbus.UInt32(1), '', timeout=600)
        except dbus.DBusException, e:
            if e._dbus_error_name == 'org.freedesktop.DBus.Error.ServiceUnknown':
                # polkitd timed out, connect again
                self.polkit = None
                return self._check_polkit_privilege(sender, conn, privilege)
            else:
                raise

        if not is_auth:
            print '_check_polkit_privilege: sender %s on connection %s pid %i is not authorized for %s: %s' % (sender, conn, pid, privilege, str(details))
            raise PermissionDeniedByPolicy(privilege)
        else:
            if int(pid) not in self.auth_pid_cache :
                self.auth_pid_cache.append(int(pid))

    # org.gnome.Nanny
    # --------------------------------------------------------------
    
    @dbus.service.method("org.gnome.Nanny",
                         in_signature='', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def IsUnLocked(self, sender=None, conn=None):
        # get peer PID
        if self.dbus_info is None:
            self.dbus_info = dbus.Interface(conn.get_object('org.freedesktop.DBus',
                '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        pid = self.dbus_info.GetConnectionUnixProcessID(sender)

        if int(pid) in self.auth_pid_cache :
            return True
        else:
            return False

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def UnLock(self, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        if self.dbus_info is None:
            self.dbus_info = dbus.Interface(conn.get_object('org.freedesktop.DBus',
                '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        pid = self.dbus_info.GetConnectionUnixProcessID(sender)

        if int(pid) in self.auth_pid_cache :
            return True
        else:
            return False

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='', out_signature='a(sss)')
    def ListUsers(self):
        return self.quarterback.usersmanager.get_users()

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sia{sa(ss)}', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def SetBlocks(self, user_id, app_id, blocks, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        self.quarterback.set_blocks(str(user_id), int(app_id), blocks)
        return True

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='a{sa(ss)}')
    def GetBlocks(self, user_id, app_id) :
        return self.quarterback.get_blocks(user_id, app_id)

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='s', out_signature='a{i(bii)}')
    def GetBlockStatusByUID(self, user_id) :
        return self.quarterback.get_block_status_by_uid(str(user_id))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='b')
    def IsAllowedToUse(self, user_id, app_id) :
        return self.quarterback.is_allowed_to_use(user_id, app_id)

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='b')
    def IsForcedToClose(self, user_id, app_id) :
        return self.quarterback.is_forced_to_close(user_id, app_id)

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sib', out_signature='')
    def SetForcedToClose(self, user_id, app_id, state) :
        self.quarterback.set_forced_to_close(user_id, app_id, state)

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='bi')
    def IsBlocked(self, user_id, app_id) :
        return self.quarterback.is_blocked(user_id, app_id)

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='bs', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def SetActiveWCF(self, active, uid, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        self.quarterback.set_wcf(bool(active), str(uid))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='', out_signature='as')
    def ListWCF(self):
        return self.quarterback.list_wcf_uids()

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sii', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def SetMaxUseTime(self, user_id, app_id, mins, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        self.quarterback.set_max_use_time(str(user_id), int(app_id), int(mins))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sii', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def AddUseTime(self, user_id, app_id, mins, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        self.quarterback.add_available_time(str(user_id), int(app_id), int(mins))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='i')
    def GetMaxUseTime(self, user_id, app_id):
        return self.quarterback.get_max_use_time(user_id, app_id)

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='i')
    def GetUseTime(self, user_id, app_id):
        return self.quarterback.get_available_time(user_id, app_id)

    @dbus.service.signal("org.gnome.Nanny",
                         signature='')
    def UpdateUsersInfo(self):
        pass

    def __UpdateUsersInfo_cb(self, quarterback):
        self.UpdateUsersInfo()

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sbi', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def SetChoreSettings(self, uid, active, limit, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        self.quarterback.set_chore_settings(str(uid), bool(active), int(limit))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='s', out_signature='bi')
    def GetChoreSettings(self, uid):
        return self.quarterback.get_chore_settings(str(uid))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='s', out_signature='b')
    def IsChoreAvailable(self, user_id) :
        return self.quarterback.is_chore_available(user_id)

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='i', out_signature='i')
    def GetActivatedChoreReward(self, chore_id):
        return self.quarterback.chore_manager.get_activated_chore_reward(chore_id)


    @dbus.service.method("org.gnome.Nanny",
                         in_signature='ssi', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def AddChoreDescription(self, title, description, reward, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.chore_manager.add_chore_description(unicode(title), unicode(description), int(reward))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='i', out_signature='a(issi)')
    def ListChoreDescriptions(self, desc_id):
        return self.quarterback.chore_manager.list_chore_descriptions(int(desc_id))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='i', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def RemoveChoreDescription(self, list_id, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.chore_manager.remove_chore_description(int(list_id))
    
    @dbus.service.method("org.gnome.Nanny",
                         in_signature='issi', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def UpdateChoreDescription(self, list_id, title, description, reward, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.chore_manager.update_chore_description(int(list_id),
                                                                    unicode(title),
                                                                    unicode(description),
                                                                    int(reward))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='is', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def AddChore(self, chore_id, uid, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.chore_manager.add_chore(int(chore_id), str(uid))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='sbbb', out_signature='a(iisiiiss)',
                         sender_keyword='sender', connection_keyword='conn')
    def ListChores(self, uid, available, contracted, finished, sender=None, conn=None):
        return self.quarterback.chore_manager.list_chores(str(uid), bool(available), bool(contracted), bool(finished))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='i', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def RemoveChore(self, list_id, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.chore_manager.remove_chore(int(list_id))
    
    @dbus.service.method("org.gnome.Nanny",
                         in_signature='iisii', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def UpdateChore(self, list_id, chore_id, uid, contracted, finished, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.chore_manager.update_chore(int(list_id),
                                                            int(chore_id),
                                                            str(uid),
                                                            int(contracted),
                                                            int(finished))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='isi', out_signature='b')
    def ContractChore(self, list_id, uid, contracted):
        return self.quarterback.chore_manager.contract_chore(int(list_id),
                                                            str(uid),
                                                            int(contracted))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='si', out_signature='')
    def TakeMercy(self, user_id, app_id):
        self.quarterback.take_mercy(str(user_id), int(app_id))

    @dbus.service.method("org.gnome.Nanny",
                         in_signature='ii', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def FinishChore(self, list_id, finished, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.chore_manager.finish_chore(int(list_id),
                                                            int(finished))

    # org.gnome.Nanny.Notification
    # --------------------------------------------------------------

    @dbus.service.signal("org.gnome.Nanny.Notification",
                         signature='bsiiib')
    def UserNotification(self, block_status, user_id, app_id, next_change, available_time, active):
        pass

    def __UserNotification_cb(self, quarterback, block_status, user_id, app_id, next_change, available_time, active):
        self.UserNotification(block_status, user_id, app_id, next_change, available_time, active)


    # org.gnome.Nanny.WebDatabase
    # --------------------------------------------------------------

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='sbsss', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def AddCustomFilter(self, uid, is_black, name, description, regex, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.filter_manager.add_custom_filter(str(uid), bool(is_black), unicode(name),
                                                                          unicode(description), unicode(regex))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='s', out_signature='a(isssb)')
    def ListCustomFilters(self, uid):
        return self.quarterback.filter_manager.list_custom_filters(int(uid))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='i', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def RemoveCustomFilter(self, list_id, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.filter_manager.remove_custom_filter(int(list_id))

    
    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='isss', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def UpdateCustomFilter(self, list_id, name, description, regex, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.filter_manager.update_custom_filter(int(list_id),
                                                                    unicode(name),
                                                                    unicode(description),
                                                                    unicode(regex))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='s', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def AddPkgFilter(self, path, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.filter_manager.add_pkg_filter(str(path))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='s', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def RemovePkgFilter(self, pkg_id, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.filter_manager.remove_pkg_filter(str(pkg_id))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='s', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def UpdatePkgFilter(self, pkg_id, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.filter_manager.update_pkg_filter(str(pkg_id))
    
    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='', out_signature='as')
    def ListPkgFilters(self):
        return self.quarterback.filter_manager.list_pkg_filter()

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='s', out_signature='a{sv}')
    def GetPkgFilterMetadata(self, pkg_id):
        return self.quarterback.filter_manager.get_pkg_filter_metadata(str(pkg_id))

#     @dbus.service.method("org.gnome.Nanny.WebDatabase",
#                          in_signature='sss', out_signature='b',
#                          sender_keyword='sender', connection_keyword='conn')
#     def SetPkgFilterMetadata(self, pkg_id, name, description, sender=None, conn=None):
#         self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
#         return self.quarterback.filter_manager.set_pkg_filter_metadata(str(pkg_id), unicode(name), unicode(description))

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='ss', out_signature='a(sb)')
    def GetPkgFilterUserCategories(self, pkg_id, uid):
        return self.quarterback.filter_manager.get_pkg_filter_user_categories(unicode(pkg_id),
                                                                              str(uid)
                                                                              )

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='ssas', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def SetPkgFilterUserCategories(self, pkg_id, uid, list_categories, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        list_c = []
        for x in list_categories :
            list_c.append(unicode(x))
            
        return self.quarterback.filter_manager.set_pkg_filter_user_categories(unicode(pkg_id),
                                                                              str(uid),
                                                                              list_c)

    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='ss', out_signature='bbas')
    def CheckDomain(self, uid, domain):
        return self.quarterback.filter_manager.check_domain(uid, domain)
                                                                              
    @dbus.service.method("org.gnome.Nanny.WebDatabase",
                         in_signature='ssss', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def AddDansGuardianList(self, uid, name, description, list_url, sender=None, conn=None):
        self._check_polkit_privilege(sender, conn, 'org.gnome.nanny.admin')
        return self.quarterback.webcontent_filter.webdb.add_dans_guardian_list(str(uid),
                                                                               unicode(name),
                                                                               unicode(description),
                                                                               unicode(list_url))
                                                                               

