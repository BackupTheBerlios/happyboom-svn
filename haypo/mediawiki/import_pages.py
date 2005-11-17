#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import sys, os, re, types
#from elementtree.ElementTree import ElementTree
from xml.dom.minidom import parseString
from xml.dom.minidom import parseString
from xml.parsers.expat import ParserCreate
from xml import sax
from subprocess import Popen, PIPE
import urllib

def usage():
    print "Usage: %s import <base url>" % sys.argv[0]
    print "    or %s export <base url>" % sys.argv[0]
    print ""
    print "Eg. of base url: http://www.haypocalc.com/wiki/"
    print "    => will use http://www.haypocalc.com/wiki/Special:Allpages"
    sys.exit(1)

def escapeshellarg(arg):
    # TODO (use os.<the right function>)
    arg = arg.replace("\\", "\\\\").replace("'", "\\'")
    return "'"+arg+"'"

def error(msg):
    print msg

def warning(msg):
    print msg

def download(url, params={}):
    params = urllib.urlencode(params)
    f = urllib.urlopen(url, params)
    return f.read()

def getAllpages(url, namespace):
    pages = download(url+"Special:Allpages", {"namespace": namespace})
    if pages == None:
        return None

    # Work around MediaWiki 1.4 bug (don't escape "&" chararacter)
    pages = re.sub("&([^a-zA-Z])", r"&amp;\1", pages)

    xml = parseString(pages)
    root = xml.documentElement
    tables = root.getElementsByTagName('table')
    assert len(tables) == 2
    table = tables[1]
    links = table.getElementsByTagName('a')
    pages = []
    for link in links:
        page = link.getAttribute('href').encode("ASCII")
        page = page.split("/")
        page = urllib.unquote(page[-1])
        if type(page) == types.UnicodeType:
            page = page.encode("UTF-8")            
        pages.append( page )
    return pages

def importNamespace(url, dir, namespace, only_last):
    print "Download document list."
    pages = getAllpages(url, namespace)
    if pages == None:
        print "Error: Can't get document list."
        sys.exit(1)
    if len(pages) == 0:
        print "(empty)"
        return
    print "Download XML data (%u documents) ..." % len(pages)
    args = { \
        "action": "submit",
        "pages": "\n".join(pages)
    }
    if only_last:
        args["curonly"] = "on"
    data = download(url+"Special:Export", args)
    if data == None:
        error("Fail to download namespace %s." % namespace)
        sys.exit(1)
    filename = os.path.join(dir, "namespace_%s.xml" % namespace)
    f = open(filename, 'w')
    f.write(data)
    f.close()

def importPages(url, only_last=False):
    # Add "/" prefix to url if needed
    if url[-1] != "/":
        url = url + "/"

    # Create pages/ if needed
    dir = "pages"
    try:
      os.mkdir(dir)
    except OSError, err:
        if err[0] != 17:
            raise

    # Which namespaces have to be downloaded?
    namespaces = range(0,16)
    namespaces.remove(8) # MediaWiki
    namespaces.remove(9) # Talk:MediaWiki
    
    # Download each namespace
    i = 1
    for namespace in namespaces: 
        print "================== Import namespace %u (%u/%u) ============== " \
                % (namespace, i, len(namespaces))
        importNamespace(url, dir, namespace, only_last)
        i = i + 1

def exportPages(url):
    print "TODO"

def main():
    if len(sys.argv) != 2:
        usage()
    url = sys.argv[1]
    try:
        importPages(url)
    except KeyboardInterrupt:
        print "Interrupted (CTRL+C): be carefull, download incomplete!"
        sys.exit(1)

if __name__=="__main__":
    main()        
