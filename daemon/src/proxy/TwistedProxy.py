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

from twisted.internet import reactor
from twisted.web import proxy, resource, server
from twisted.enterprise import adbapi
from twisted.application import internet, service
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


if os.name == "posix" :
    BAD_CONTENT_TMP_DIR = "/var/tmp/nanny/"
elif os.name == "nt" :
    BAD_CONTENT_TMP_DIR = "C:\\WINDOWS\\nanny_data\\tmp"

class BadBoyResponseFilter:
    def __init__(self, client):
        if not os.path.exists(BAD_CONTENT_TMP_DIR) :
            try:
                os.makedirs(BAD_CONTENT_TMP_DIR)
            except:
                pass
        
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
        try:
            proxy.ProxyClient.handleResponseEnd(self)
        except:
            print "Twisted E> handleResponseEnd"


class ProxyClientFactory(proxy.ProxyClientFactory):
    def buildProtocol(self, addr):
        client = proxy.ProxyClientFactory.buildProtocol(self, addr)
        client.__class__ = ProxyClient
        return client

class ReverseProxyResource(resource.Resource) :

    proxyClientFactoryClass = ProxyClientFactory

    def __init__(self, uid, filter_manager, reactor=reactor, domain_level=0, pre_check=[False, False]):
        resource.Resource.__init__(self)
        self.reactor = reactor
        self.uid = uid
        self.url = ''
        self.filter_manager = filter_manager
        self.domain_level = domain_level
        self.pre_check = pre_check
        self.domains_blocked_cache = {}
        
    def getChild(self, path, request):
        pre_check=[False, False]
        host, port = self.__get_host_info(request)
        if self.domain_level ==0 :
            ts = reactor.seconds()
            
            if self.domains_blocked_cache.has_key(host) and ( ts - self.domains_blocked_cache[host][0] ) <= 10  :
                print self.domains_blocked_cache[host][1]
                block_d = BlockingDeferred(self.domains_blocked_cache[host][1])
                try:
                    pre_check, categories = block_d.blockOn()
                    print "Host %s , verified [cached] (pre_check=%s)" % (host, pre_check)
                except:
                    print "Something wrong validating domain %s" % host
                    pre_check = [False, False]
            else:
                query = self.filter_manager.check_domain_defer(self.uid, host)
                self.domains_blocked_cache[host]=[reactor.seconds(), query]
                
                block_d = BlockingDeferred(query)
                try:
                    pre_check, categories = block_d.blockOn()
                    print "Host %s , verified (pre_check=%s)" % (host, pre_check)
                except:
                    print "Something wrong validating domain %s" % host
                    pre_check = [False, False]
                
            return ReverseProxyResource(self.uid, self.filter_manager, reactor=reactor,
                                        domain_level=self.domain_level + 1,
                                        pre_check=pre_check)
        else:
            return ReverseProxyResource(self.uid, self.filter_manager, reactor=reactor,
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

        d = self.filter_manager.check_url_defer (self.uid, host, port, request, rest, self.pre_check)
        d.addCallback(self.__validate_request_cb)

        return server.NOT_DONE_YET
 
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

