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

import os
import sys
import gtk

def ui_magic(object, ui_file, prefix):
     main_ui_filename = ui_file
     object.xml = gtk.Builder ()
     object.xml.add_from_file (main_ui_filename)
     objects = object.xml.get_objects()
     for content in objects:
          try:
               if isinstance(content, gtk.Label):
                    if content.get_label() != None and len(content.get_label()) > 0 :
                         content.set_markup(_(content.get_label()))
               elif isinstance(content, gtk.Button):
                    if content.get_label() != None and len(content.get_label()) > 0 :
                         content.set_label(_(content.get_label()))
               else:
                    if content.get_text() != None and len(content.get_text()) > 0 :
                         content.set_text(_(content.get_text()))
          except AttributeError:
               pass

     # This is a workarround. For some reason obj.get_name don't return 
     # the real name of the widget
     from xml.etree.ElementTree import ElementTree 
     xml = ElementTree()
     xml.parse(main_ui_filename)
     for obj in xml.findall ('//object'):
          try:
               if obj.attrib["id"].startswith(prefix) :
                    widget = object.xml.get_object(obj.attrib["id"])
                    widget_name = obj.attrib["id"][len(prefix)+1:]
                    exec ('object.%s = widget' % widget_name)
          except:
               print "Something fails at ui_magic"

def is_win32user_an_admin():
     WHO_AM_I = "C:\\WINDOWS\\System32\\whoami.exe"
     if not os.path.exists(WHO_AM_I) :
          import win32security
          import ntsecuritycon
          subAuths = ntsecuritycon.SECURITY_BUILTIN_DOMAIN_RID, \
              ntsecuritycon.DOMAIN_ALIAS_RID_ADMINS
          sidAdmins = win32security.SID(ntsecuritycon.SECURITY_NT_AUTHORITY, subAuths)
          return win32security.CheckTokenMembership(None, sidAdmins)
     else:
          import subprocess

          p = subprocess.Popen([WHO_AM_I, "/GROUPS", "/SID"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          if p.wait () != 0 :
               p = subprocess.Popen([WHO_AM_I, "/GROUPS"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
               if p.wait () != 0 :
                    return False

          for line in p.stdout.readlines() :
               if "S-1-5-32-544 " in line or "S-1-5-32-544\r\n" in line :
                    return True

          return False


def check_win32_admin():
    if is_win32user_an_admin() == False:
         msg = gtk.MessageDialog(parent=None, flags=0,
                                 type=gtk.MESSAGE_INFO,
                                 buttons=gtk.BUTTONS_CLOSE, message_format=None)
         msg.set_markup(u"<b>%s</b>" % _(u"Nanny Admin Tools requires Admin user"))
         msg.format_secondary_markup(_(u"To run any Nanny Admin Tool you must to be admin of the system."))
         ret = msg.run()
         msg.destroy()
         
         sys.exit(0)
