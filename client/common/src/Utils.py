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
import gtk

def ui_magic(object, ui_file, prefix):
     main_ui_filename = ui_file
     object.xml = gtk.Builder ()
     object.xml.add_from_file (main_ui_filename)
     objects = object.xml.get_objects()
     for content in objects:
          try:
               print content.get_name()
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
          
          if isinstance (content, gtk.Widget):
               widget_name = content.get_name ()
               if widget_name.startswith (prefix):
                    widget_name = widget_name[len(prefix)+1:]
                    exec ('object.%s = content' % widget_name)
                    
