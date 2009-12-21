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


from twisted.internet import reactor

import os
import urllib2
import tarfile

class UrlImporter:
    def __init__(self, origin_name, uid, description):
        from Controllers import WebDatabase

        self.file_path = ''
        self.web_db = WebDatabase()
        self.uid = uid
        self.origin_name = origin_name
       
        self.web_db.add_origin(origin_name, uid, description)

    def get_url(self, url, file_path):
        if file_path is not '':
            self.file_path = file_path
        else:
            self.file_path = '/tmp/urls.tar.gz'

        openurl = urllib2.urlopen(url)
        file = open(self.file_path,'wb')
        file.write(openurl.read())
        file.close()
        
        return self.file_path

    def import_tar_file(self, file):
        tar = tarfile.open(file)
        tar.extractall('/tmp/nanny')
        tar.close()

        for root, dirs, files in os.walk('/tmp/nanny/'):
            for file in files:
                path = root + '/' + file
                category = path.split('/')[-2]   # Last folder of the path is category.
                type = file[:-1] 
                self.import_file(category, type, path)

    def import_file(self, category, type, filepath):
        file = open(filepath)
        for line in file:
            line = line[:-1]                # Clean out the newline character.
            if self.is_a_url(line):
                self.web_db.add_web(False, 'black', self.uid, category, type,
                                    self.origin_name, self.origin_name, line)

    def is_a_url(self, url):
        if len(url) > 0:
            return True

if __name__ == '__main__':
#    url = 'http://urlblacklist.com/cgi-bin/commercialdownload.pl' + \
#          '?type=download&file=bigblacklist'
    url = 'http://urlblacklist.com/cgi-bin/commercialdownload.pl' + \
          '?type=download&file=smalltestlist'

    importer = Importer('dansguardian', 0, 'dansguardian filter list')
    file = importer.get_url(url, '')
    importer.import_tar_file(file)

    reactor.run()
