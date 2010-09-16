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
from QuarterBack import QuarterBack

if os.name == "posix":
    from NannyDBus import NannyDBus
elif os.name == "nt":
    from NannyPyroBus import start_pyro_bus
import nanny.daemon.proxy

import signal
import sys
import os

class Daemon :
    def __init__(self, app):
        self.quarterback = QuarterBack(app)

        if os.name == "posix" :
            self.bus = NannyDBus(self.quarterback)
	elif os.name == "nt" :
            from twisted.internet import reactor
            start_pyro_bus(self.quarterback)
        

