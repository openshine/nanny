#!/usr/bin/env python
# Copyright (C) 2009 Roberto Majadas, Cesar Garcia, Luis de Bethencourt
# <openshine.com>
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

#Add nanny module to python paths
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nanny_lib_path = os.path.join(root_path, "lib", "python2.6", "site-packages")
sys.path.append(nanny_lib_path)

print sys.path
import nanny
