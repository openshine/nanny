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
import time
import tempfile
import tarfile

import gobject
import gio

import sqlite3

from hachoir_regex import PatternMatching

def try_to_str(string):
    try:
        return str(string)
    except:
        print "Error importing : %s" % string
        return None

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
        t0 = time.time()
        self.__create_sqlite()
        self.__copy_dansguardian_file()
        self.__dansguardian_2_sqlite()
        self.conn.close()
        self.emit("progress-status", 100, _("Blacklist imported"))
        
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
        self.emit("progress-status", 1, _("Nanny file created"))

    def __download_dansguardian_progress_cb(self, current, total, data):
        self.emit("progress-status", 2, _("Downloading file (%s%%)" % ((current * 100)/total)) )
    def __copy_dansguardian_file(self):
        self.tmp_dansguardian = os.path.join(tempfile.mkdtemp(), os.path.basename(self.in_url))
        gio.File(self.in_url).copy(gio.File(self.tmp_dansguardian),
                                   self.__download_dansguardian_progress_cb,
                                   0, None, None)

    def __dansguardian_2_sqlite(self):
        tfile = tarfile.open(self.tmp_dansguardian)
        self.dg_files = 0
        self.dg_current_file = 0
        
        for member in tfile :
            if (os.path.basename(member.name) == "urls" or os.path.basename(member.name) == "domains") and member.isfile():
               self.dg_files = self.dg_files + 1
               
        for member in tfile :
            m_fd = None
            if "whitelist" in member.name.lower() :
                is_black = False
            else:
                is_black = True

            if os.path.basename(member.name) == "urls" and member.isfile():
                self.dg_current_file = self.dg_current_file + 1
                m_fd = tfile.extractfile(member.name)
                itype = "url"
                category = os.path.basename(os.path.dirname(member.name))
                t0 = time.time()
                self.__add_items_2_sqlite(m_fd, category, is_black, itype)
                
            elif os.path.basename(member.name) == "domains" and member.isfile():
                self.dg_current_file = self.dg_current_file + 1
                m_fd = tfile.extractfile(member.name)
                itype = "domain"
                category = os.path.basename(os.path.dirname(member.name))
                t0 = time.time()
                self.__add_items_2_sqlite(m_fd, category, is_black, itype)
            else:
                continue

    def __add_items_2_sqlite(self, fd, category, is_black, itype):
        if itype == "domain" :
            domains = []
            for line in fd.readlines() :
                dg_domain=line.replace("\r","").replace("\n", "").replace(" ","")
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
            total = len(domains)
            current = 0
            
            for domain in domains :
                string = try_to_str(domain)
                if string == None :
                    continue
                
                p.addString(string)
                i = i + 1
                current = current + 1 
                if i < 1500 :
                    continue
                
                if step == False and i % 500 == 0 :
                    if len(str(p.regex)) > 20000 :
                        if len(str(p.regex)) > 24000 :
                            self.__insert_domain_into_sqlite(category, str(p.regex), is_black, current, total )
                            p = PatternMatching()
                            step = False
                            i = 0
                            continue
                        
                        step = True
                        continue
                    
                elif step == True and i % 100 == 0 :
                    if len(str(p.regex)) > 25000 :
                        self.__insert_domain_into_sqlite(category, str(p.regex), is_black, current, total)
                        p = PatternMatching()
                        step = False
                        i = 0
            
            if len(str(p.regex)) > 0 :
                self.__insert_domain_into_sqlite(category, str(p.regex), is_black, total, total)
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
            current = 0
            if is_black == True :
                total = len(urls) + len(domain_set)
            else:
                total = len(urls)

            for url in urls :
                string = try_to_str(url)
                if string == None :
                    continue
                
                p.addString(string)
                i = i + 1
                current = current + 1
                
                if i % 100 == 0 :
                    if len(str(p.regex)) > 25000 :
                        self.__insert_url_into_sqlite(category, str(p.regex), is_black, current, total)
                        p = PatternMatching()
                        i = 0

            if len(str(p.regex)) > 0 :
                self.__insert_url_into_sqlite(category, str(p.regex), is_black, len(urls) , total)
                
            if is_black == True:
                domains = list(domain_set)
                domains.sort()

                p = PatternMatching()
                i = 0
                step = False

                for domain in domains :
                    string = try_to_str(domain)
                    if string == None :
                        continue
                    
                    p.addString(string)
                    i = i + 1
                    current = current + 1
                    if i < 1500 :
                        continue
                    
                    if step == False and i % 500 == 0 :
                        if len(str(p.regex)) > 20000 :
                            if len(str(p.regex)) > 24000 :
                                self.__insert_domain_into_sqlite("may_url_blocked", str(p.regex), is_black, current, total)
                                p = PatternMatching()
                                step = False
                                i = 0
                                continue
                                
                            step = True
                            continue

                    elif step == True and i % 100 == 0 :
                        if len(str(p.regex)) > 25000 :
                            self.__insert_domain_into_sqlite("may_url_blocked", str(p.regex), is_black, current, total)
                            p = PatternMatching()
                            step = False
                            i = 0

                if len(str(p.regex)) > 0 :
                    self.__insert_domain_into_sqlite("may_url_blocked", str(p.regex), is_black, total, total)        
            

    def __insert_domain_into_sqlite(self, category, regexp, is_black, current, total):
        try:
            c = self.conn.cursor()
            if is_black == True :
                c.execute('insert into black_domains values ("%s", "%s")' % (category, regexp))
            else:
                c.execute('insert into white_domains values ("%s", "%s")' % (category, regexp))

            self.conn.commit()
            self.emit("progress-status",
                      (self.dg_current_file * 97 / self.dg_files) + 2,
                      _("Importing domains [category: %s] (%s%%)" % (category, current * 100 / total)))
                      
        except :
            print "Something wrong in sqlite inserting domains :\nCategory : %s\nREGEX %s" (category, regexp)

    def __insert_url_into_sqlite(self, category, regexp, is_black, current, total):
        try:
            c = self.conn.cursor()
            if is_black == True :
                c.execute('insert into black_urls values ("%s", "%s")' % (category, regexp))
            else:
                c.execute('insert into white_urls values ("%s", "%s")' % (category, regexp))
        
            self.conn.commit()
            self.emit("progress-status",
                      (self.dg_current_file * 97 / self.dg_files) + 2,
                      _("Importing urls [category: %s] (%s%%)" % (category, current * 100 / total)))
        except :
            print "Something wrong in sqlite inserting urls :\nCategory : %s\nREGEX %s" (category, regexp)
            
gobject.type_register(DansGuardianImporter)

if __name__ == '__main__':
    import gettext
    import __builtin__
    __builtin__._ = gettext.gettext
    
    def progress_cb(dg, percent, status_msg, data):
        print "[%s%%] -> %s" % (percent, status_msg)
    
    d = DansGuardianImporter("/var/www/pets.tgz","/tmp/pets.sqlite")
    d.connect("progress-status", progress_cb, None)
    d.run()
