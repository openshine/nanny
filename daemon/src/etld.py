#!/usr/bin/python

# Copyright (c) 2009 Michael Still
# Released under the terms of the GNU GPL v2

# Mozilla publishes a rule file which may be used to calculate effective TLDs
# at:
#
#   http://mxr.mozilla.org/mozilla-central/source/netwerk/dns/src/
#   effective_tld_names.dat?raw=1
#
# Use that file to take a domain name and return a (domain, etld) tuple.
# Documentation for the rule file format is at:
#
#   https://wiki.mozilla.org/Gecko:Effective_TLD_Service

import os
import re
import sys
import time
from urlparse import urlparse

with open (os.path.join (os.path.dirname(__file__), 'effective_tld_names.dat')) as tldFile:
    TLDS = set([line.strip() for line in tldFile if line[0] not in "/\n"])

class etld(object):
    """Helper to determine the effective TLD portion of a domain name."""
    
    def __init__(self, datafile='effective_tld_names.dat'):
        """Load the data file ready for lookups."""
        
        self.tlds = TLDS
        
    def parse(self, hostname):
        """Parse a hostanme into domain and etld portions."""

        urlElements = urlparse(hostname)[1].split('.')
        # urlElements = ["abcde","co","uk"]

        for i in range(-len(urlElements),0):
            lastIElements = urlElements[i:]
            #    i=-3: ["abcde","co","uk"]
            #    i=-2: ["co","uk"]
            #    i=-1: ["uk"] etc

            candidate = ".".join(lastIElements) # abcde.co.uk, co.uk, uk
            wildcardCandidate = ".".join(["*"]+lastIElements[1:]) # *.co.uk, *.uk, *
            exceptionCandidate = "!"+candidate

            # match tlds: 
            if (exceptionCandidate in self.tlds):
                return (".".join (urlElements[:i]), ".".join(urlElements[i:]))
            if (candidate in self.tlds or wildcardCandidate in self.tlds):
                return (".".join (urlElements[:i-1]), ".".join(urlElements[i-1:]))
                # returns "abcde.co.uk"

        raise ValueError("Domain not in global list of TLDs")
