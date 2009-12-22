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
from twisted.web import proxy, resource, server
from twisted.enterprise import adbapi
from twisted.application import internet, service
from twisted.python.lockfile import FilesystemLock, isLocked
from twisted.internet.defer import DeferredFilesystemLock 
import urlparse
from urllib import quote as urlquote

import os
from tempfile import TemporaryFile, gettempdir
import time

import Image, ImageDraw, ImageFilter

from Controllers import BlockingDeferred

BAD_WEB_TEMPLATE='''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
  <link href="http://www.gnome.org/css/layout.css" rel="stylesheet" type="text/css" media="screen">
  <link href="http://www.gnome.org/css/style.css" rel="stylesheet" type="text/css" media="all">
  <link rel="icon" type="image/png" href="http://www.gnome.org/img/logo/foot-16.png">
  <link rel="SHORTCUT ICON" type="image/png" href="http://www.gnome.org/img/logo/foot-16.png">

	<title>Nanny Parental Control</title>
	<link rel="stylesheet" type="text/css" href="http://www.gnome.org/frontpage.css">

</head>

<body>
<div id="page">
    <div id="header">
      <h1>Nanny Parental Control</h1>
    </div> 
</div>
</body>
'''

BAD_CONTENT_TMP_DIR="/var/tmp/nanny"

class BadBoyResponseFilter:
    def __init__(self, client):
        if not os.path.exists(BAD_CONTENT_TMP_DIR) :
            os.system("mkdir -p %s" % BAD_CONTENT_TMP_DIR)
        
        self.fd_orig = TemporaryFile(mode='rw+b', dir=BAD_CONTENT_TMP_DIR)
        self.fd_filtered = TemporaryFile(mode='rw+b', dir=BAD_CONTENT_TMP_DIR)
        
        self.client = client

    def feed(self, data):
        self.fd_orig.write(data)

    def filter(self):
        pass
        
    def send_response(self):
        self.fd_orig.seek(0)
        self.filter()
        self.client.father.transport.write(self.client.bb_status)
        for key,value in self.client.bb_headers :
            if key.lower() == "content-length" :
                value = self.fd_filtered.tell()
            self.client.father.transport.write("%s: %s\r\n" % (key, value))

        self.client.father.transport.write("\r\n")
            
        file_len = self.fd_filtered.tell()
        self.fd_filtered.seek(0)

        while self.fd_filtered.tell() < file_len :
            self.client.father.transport.write(self.fd_filtered.read(1024))

        self.fd_orig.close()
        self.fd_filtered.close()

class BadBoyResponseFilterImage(BadBoyResponseFilter) :
    def __init__(self, client):
        BadBoyResponseFilter.__init__(self, client)

    def filter(self):
        im = Image.open(self.fd_orig)
        im_format = im.format

        draw = ImageDraw.Draw(im)
        try:
            draw.rectangle((0, 0) + im.size, fill="#FFFFFF")
        except:
            try:
                draw.rectangle((0, 0) + im.size, fill="255")
            except:
                pass
            
        draw.line((0, 0) + im.size, fill=128, width=10)
        draw.line((0, im.size[1], im.size[0], 0), fill=128, width=10)
        del draw 

        im.save(self.fd_filtered, im_format)

class BadBoyProxyClient(proxy.ProxyClient) :
    def connectionMade(self):
        self.bb_headers = []
        self.bb_response = None
        self.bb_status = None
        self.bb_status_code = None
        self.handle_response = False
        proxy.ProxyClient.connectionMade(self)
    
    def handleStatus(self, version, code, message):
        if message:
            # Add a whitespace to message, this allows empty messages
            # transparently
            message = " %s" % (message,)
        self.bb_status = "%s %s%s\r\n" % (version, code, message)
        self.bb_status_code = code
    
    def handleHeader(self, key, value):
        self.bb_headers.append((key, value))
        if self.bb_status_code != "200" :
            return
        
        if key.lower() == "content-type" :
            mime_type = value.split(";")[0]
            if mime_type.startswith('image/') :
                self.bb_response=BadBoyResponseFilterImage(self)

    def handleEndHeaders(self):
        if self.bb_response == None:
            self.father.setResponseCode(404)
            self.father.write(BAD_WEB_TEMPLATE)
            proxy.ProxyClient.handleResponseEnd(self)

    def handleResponsePart(self, data):
        if self.bb_response != None:
            self.bb_response.feed(data)

    def handleResponseEnd(self):
        if self.handle_response == True :
            return
        self.handle_response = True
 
        if self.bb_response != None:
            self.bb_response.send_response()
        
        proxy.ProxyClient.handleResponseEnd(self)

class BadBoyProxyClientFactory(proxy.ProxyClientFactory):
    def buildProtocol(self, addr):
        client = proxy.ProxyClientFactory.buildProtocol(self, addr)
        client.__class__ = BadBoyProxyClient
        return client

class ProxyClient(proxy.ProxyClient) :
    def handleHeader(self, key, value):
        proxy.ProxyClient.handleHeader(self, key, value)

    def handleResponsePart(self, data):
        proxy.ProxyClient.handleResponsePart(self, data)

    def handleResponseEnd(self):
        proxy.ProxyClient.handleResponseEnd(self)


class ProxyClientFactory(proxy.ProxyClientFactory):
    def buildProtocol(self, addr):
        client = proxy.ProxyClientFactory.buildProtocol(self, addr)
        client.__class__ = ProxyClient
        return client

class ReverseProxyResource(resource.Resource) :

    proxyClientFactoryClass = ProxyClientFactory

    def __init__(self, uid, dbpool, reactor=reactor, domain_level=0, pre_check=[False, False]):
        resource.Resource.__init__(self)
        self.reactor = reactor
        self.uid = uid
        self.url = ''
        self.dbpool = dbpool
        self.domain_level = domain_level
        self.pre_check = pre_check
        self.domains_blocked_cache = {}
        
    def getChild(self, path, request):
        pre_check=[False, False]
        host, port = self.__get_host_info(request)
        if self.domain_level ==0 :
            ts = reactor.seconds()
            
            if self.domains_blocked_cache.has_key(host) and ( ts - self.domains_blocked_cache[host][0] ) <= 120  :
                print self.domains_blocked_cache[host][1]
                block_d = BlockingDeferred(self.domains_blocked_cache[host][1])
                try:
                    pre_check = block_d.blockOn()
                    print "Host %s , verified [cached] (pre_check=%s)" % (host, pre_check)
                except:
                    print "Something wrong validating domain %s" % host
                    pre_check = [False, False]
            else:
                query = self.dbpool.runInteraction(self.__validate_site, host)
                self.domains_blocked_cache[host]=[reactor.seconds(), query]
                
                block_d = BlockingDeferred(query)
                try:
                    pre_check = block_d.blockOn()
                    print "Host %s , verified (pre_check=%s)" % (host, pre_check)
                except:
                    print "Something wrong validating domain %s" % host
                    pre_check = [False, False]
                
            return ReverseProxyResource(self.uid, self.dbpool, reactor=reactor,
                                        domain_level=self.domain_level + 1,
                                        pre_check=pre_check)
        else:
            return ReverseProxyResource(self.uid, self.dbpool, reactor=reactor,
                                        domain_level=self.domain_level + 1,
                                        pre_check=self.pre_check)

    def render(self, request):
        host, port = self.__get_host_info(request)
        request.content.seek(0, 0)

        path = urlparse.urlparse(request.uri)[2]
        qs = urlparse.urlparse(request.uri)[4]
        rest = ""
        
        if qs:
            rest = path + '?' + qs
        else:
            rest = path
            
        self.request = request

        query = self.dbpool.runInteraction(self.__validate_uri, host, port, request, rest, self.pre_check)
        query.addCallback(self.__validate_request_cb)

        return server.NOT_DONE_YET

    def __validate_site(self, txn, host):
        found = False
        block_domain = False
        may_block_url = False
        
        sql="SELECT * FROM Website WHERE uid = '%s' AND ((type = 'domain' AND '%s' GLOB body) OR (type = 'domain' AND '%s' GLOB '*.' || body) OR (type = 'url' AND body GLOB '%s'))" % (self.uid, host, host, "*" + host + "*")
        txn.execute(sql)
    	select = txn.fetchall()

        if len(select) > 0 :
            for web in select:
                if web[1] == True and web[5] == "domain" :
                    block_domain = True
                    break
            
            for web in select:
                if web[1] == True and web[5] == "url" :
                    may_block_url = True
                    break
                
            for web in select:
                if web[1] == False and web[5] == "domain" :
                    print "Domain WhiteListed : %s"  % host
                    block_domain = False
                    break
            
        return block_domain, may_block_url
 
    def __validate_uri(self, txn, host, port, request, rest, pre_check):
        if pre_check[0] == True :
            print 'Uri Validation stopped because domain is blocked, %s' % (host + request.uri)
            return False, request, rest, host, port

        if pre_check[1] == False :
            print 'Uri validation verified in pre-check %s' % (host + request.uri)
            return True, request, rest, host, port
    
        uri = host + request.uri
        is_ok = True

        sql="SELECT * FROM Website WHERE uid = '%s' AND type = 'url' AND '%s' GLOB '*' || body || '*' " % (self.uid, uri)
        txn.execute(sql)
    	select = txn.fetchall()

        if len(select) > 0 :
            for web in select:
                if web[1] == True :
                    print 'Uri blocked : %s ' % (web[6])
                    is_ok = False
                    break
            
            for web in select:
                if web[1] == False :
                    print 'Uri WhiteListed : %s ' % (web[6])
                    is_ok = False
                    break
            
        return is_ok, request, rest, host, port

    def __validate_request_cb(self, data):
        is_ok = data[0]
        request = data[1]
        rest = data[2]
        host = data[3]
        port = data[4]

        if is_ok :
            clientFactory = self.proxyClientFactoryClass(
                self.request.method, rest, request.clientproto,
                request.getAllHeaders(), request.content.read(), request)
            self.reactor.connectTCP(host, port, clientFactory)
        else:
            clientFactory = BadBoyProxyClientFactory(
                self.request.method, rest, request.clientproto,
                request.getAllHeaders(), request.content.read(), request)
            self.reactor.connectTCP(host, port, clientFactory)

    def __get_host_info(self, request):
        host = None
        port = 80

        x = request.received_headers['host'].split(":")
        if len(x) > 1 :
            host = x[0]
            port = int(x[1])
        else:
            host = x[0]

        return host, port

if __name__ == "__main__" :
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)

    dbpool = adbapi.ConnectionPool('sqlite3', '/var/lib/nanny/webs.db', check_same_thread=False)
    root = ReverseProxyResource("1001", dbpool)
    site = server.Site(root)
    reactor.listenTCP(8080, site)
    reactor.run()
