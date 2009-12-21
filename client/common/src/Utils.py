#!/usr/bin/env python

# Copyright (C) 2009 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
#   Cesar Garcia Tapia <cesar.garcia.tapia at openshine.com>
#   Luis de Bethencourt <luibg at openshine.com>
#   Pablo Vieytes <pvieytes at openshine.com>
#
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free
# Software

import os
import gtk

def glade_magic(object, glade_file, prefix):
    main_ui_filename = glade_file
    object.xml = gtk.Builder ()
    object.xml.add_from_file (main_ui_filename)
    objects = object.xml.get_objects()
    for content in objects:
        if isinstance (content, gtk.Widget):
            widget_name = content.get_name ()
            if widget_name.startswith (prefix):
                widget_name = widget_name[len(prefix)+1:]
                exec ('object.%s = content' % widget_name)
