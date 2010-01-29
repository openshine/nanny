#!/usr/bin/python

# Copyright (C) 2009 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
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
# Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import os
import tempfile
import tarfile

import gobject
import gio

import sqlite3

from hachoir_regex import PatternMatching

class DansGuardianImporter (gobject.GObject):
    __gsignals__ = {
        'progress-status' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)),
        }

    def __init__(self, in_url, out_path):
        gobject.GObject.__init__(self)
        self.in_url = in_url
        self.out_path = out_path
        self.conn = None

    def run(self):
        self.__create_sqlite()
        self.__copy_dansguardian_file()
        self.__dansguardian_2_sqlite()
        self.conn.close()

    def __create_sqlite(self):
        if os.path.exists(self.out_path) :
            gio.File(self.out_path).move(gio.File(self.out_path + ".bak"))

        self.conn = sqlite3.connect(self.out_path)
        c = self.conn.cursor()
        c.execute('create table black_domains (category text, regexp text)')
        c.execute('create table black_urls (category text, regexp text)')
        c.execute('create table white_domains (category text, regexp text)')
        c.execute('create table white_urls (category text, regexp text)')
        self.conn.commit()

    def __download_dansguardian_progress_cb(self, current, total, data):
        pass

    def __copy_dansguardian_file(self):
        self.tmp_dansguardian = os.path.join(tempfile.mkdtemp(), os.path.basename(self.in_url))
        gio.File(self.in_url).copy(gio.File(self.tmp_dansguardian),
                                   self.__download_dansguardian_progress_cb,
                                   0, None, None)

    def __dansguardian_2_sqlite(self):
        tfile = tarfile.open(self.tmp_dansguardian)
        for member in tfile :
            m_fd = None
            if "whitelist" in member.name.lower() :
                is_black = False
            else:
                is_black = True

            if os.path.basename(member.name) == "urls" and member.isfile():
                m_fd = tfile.extractfile(member.name)
                itype = "url"
                category = os.path.basename(os.path.dirname(member.name))
                self.__add_items_2_sqlite(m_fd, category, is_black, itype)
                
            elif os.path.basename(member.name) == "domains" and member.isfile():
                m_fd = tfile.extractfile(member.name)
                itype = "domain"
                category = os.path.basename(os.path.dirname(member.name))
                self.__add_items_2_sqlite(m_fd, category, is_black, itype)
                
            else:
                continue

    def __add_items_2_sqlite(self, fd, category, is_black, itype):
        if itype == "domain" :
            domains = []
            for line in fd.readlines() :
                dg_domain=line.replace("\r","").replace("\n", "").replace(" ","").decode("iso8859-15").lower()
                tmp_domain=''
                tmp_domain_item_list = dg_domain.split(".")
                tmp_domain_item_list.reverse()
                for x in tmp_domain_item_list:
                    tmp_domain = tmp_domain + x + "."
                tmp_domain=tmp_domain[:-1]
                domains.append(tmp_domain)
            
            domains.sort()

            p = PatternMatching()
            i = 0
            step = False
            
            for domain in domains :
                p.addString(str(domain))
                i = i + 1
                if step == False and i % 500 == 0 :
                    if len(str(p.regex)) > 20000 :
                        step = True
                        continue
                    
                elif step == True and i % 100 == 0 :
                    if len(str(p.regex)) > 30000 :
                        print "Domains -> To sqlite!! (%s, %s)"  % (i, len(str(p.regex)))
                        self.__insert_domain_into_sqlite(category, str(p.regex), is_black)
                        p = PatternMatching()
                        step = False
                        i = 0
            
            if len(str(p.regex)) > 0 :
                print "Domains -> To sqlite!! (%s, %s)"  % (i, len(str(p.regex)))
                self.__insert_domain_into_sqlite(category, str(p.regex), is_black)
        else:
            domain_set = set()
            
            urls = []
            for line in fd.readlines() :
                dg_url = line.replace("\r","").replace("\n", "").replace(" ","").decode("iso8859-15").lower()
                urls.append(dg_url)

                if is_black == True:
                    tmp_domain=''
                    tmp_domain_item_list = dg_url.split("/")[0].split(".")
                    tmp_domain_item_list.reverse()
                    for x in tmp_domain_item_list:
                        tmp_domain = tmp_domain + x + "."
                        tmp_domain=tmp_domain[:-1]                
                        domain_set.add(tmp_domain)

            urls.sort()
            
            p = PatternMatching()
            i = 0

            for url in urls :
                p.addString(str(url))
                i = i + 1

                if i % 100 == 0 :
                    if len(str(p.regex)) > 30000 :
                        print "Urls -> To sqlite!! (%s, %s)"  % (i, len(str(p.regex)))
                        self.__insert_url_into_sqlite(category, str(p.regex), is_black)
                        p = PatternMatching()
                        i = 0

            if len(str(p.regex)) > 0 :
                print "Urls -> To sqlite!! (%s, %s)"  % (i, len(str(p.regex)))
                self.__insert_url_into_sqlite(category, str(p.regex), is_black)
                
            if is_black == True:
                domains = list(domain_set)
                domains.sort()

                p = PatternMatching()
                i = 0
                step = False

                for domain in domains :
                    p.addString(str(domain))
                    i = i + 1
                    if step == False and i % 500 == 0 :
                        if len(str(p.regex)) > 20000 :
                            step = True
                            continue

                    elif step == True and i % 100 == 0 :
                        if len(str(p.regex)) > 30000 :
                            print "May url block -> To sqlite!! (%s, %s)"  % (i, len(str(p.regex)))
                            self.__insert_domain_into_sqlite("may_url_blocked", str(p.regex), is_black)
                            p = PatternMatching()
                            step = False
                            i = 0

                if len(str(p.regex)) > 0 :
                    print "May url block -> To sqlite!! (%s, %s)"  % (i, len(str(p.regex)))
                    self.__insert_domain_into_sqlite("may_url_blocked", str(p.regex), is_black)        
            

    def __insert_domain_into_sqlite(self, category, regexp, is_black):
        c = self.conn.cursor()
        if is_black == True :
            c.execute('insert into black_domains values ("%s", "%s")' % (category, regexp))
        else:
            c.execute('insert into white_domains values ("%s", "%s")' % (category, regexp))

        self.conn.commit()

    def __insert_url_into_sqlite(self, category, regexp, is_black):
        c = self.conn.cursor()
        if is_black == True :
            c.execute('insert into black_urls values ("%s", "%s")' % (category, regexp))
        else:
            c.execute('insert into white_urlss values ("%s", "%s")' % (category, regexp))

        self.conn.commit()
            
gobject.type_register(DansGuardianImporter)

if __name__ == '__main__':
    d = DansGuardianImporter("/var/www/prueba3.tgz","/tmp/prueba.sqlite")
    d.run()
