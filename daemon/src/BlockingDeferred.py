#!/usr/bin/env python

# Copyright (C) 2009 Junta de Andalucia
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

from twisted.internet import reactor, defer
from twisted.internet.defer import AlreadyCalledError
from twisted.python import failure
from twisted.web import client


TIMEOUT = 0.05                  # Set the timeout for poll/select

class BlockingDeferred(object):
    """Wrap a Deferred into a blocking API."""
    
    def __init__(self, d):
        """Wrap a Deferred d."""
        self.d = d
        self.finished = False
        self.count = 0

    def blockOn(self):
        """Call this to block and get the result of the wrapped Deferred.
        
        On success this will return the result.
        
        On failure, it will raise an exception.
        """
        
        self.d.addBoth(self.gotResult)
        self.d.addErrback(self.gotFailure)
        
        while not self.finished:
            reactor.iterate(TIMEOUT)
            self.count += 1
        
        if isinstance(self.d.result, dict):
            f = self.d.result.get('failure', None)
            if isinstance(f, failure.Failure):
                f.raiseException()
        return self.d.result

    def gotResult(self, result):
        self.finished = True
        return result
        
    def gotFailure(self, f):
        self.finished = True
        # Now make it look like a success so the failure isn't unhandled
        return {'failure':f}
