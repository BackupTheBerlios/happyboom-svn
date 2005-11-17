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
        pages.append( page[-1] )
    return pages

def cleanupUrl(url):
    name = urllib.unquote(url)
    if type(name) != types.UnicodeType:
        name = unicode(name,"UTF-8")
    return name.replace("_", " ")

def importNamespace(url, dir, namespace, only_last):
    print "Download list of pages ..."
    pages = getAllpages(url, namespace)
    if pages == None:
        print "Error: Can't get list of pages."
        sys.exit(1)
    i = 1
    for page in pages:
        print "Download \"%s\" (%u/%u) ..." \
                % (cleanupUrl(page), i, len(pages))
        args = {"action": "submit", "pages": page}
        if only_last:
            args["curonly"] = "on"
        data = download(url+"Special:Export", args)
        if data == None:
            error("Fail to download page \"%s\"." % page)
            sys.exit(1)
        filename = os.path.join(dir, page)
        f = open(filename, 'w')
        f.write(data)
        f.close()
#        print "  \--> saved into \"%s\"." % (filename) 
        i = i + 1

def importPages(url, only_last=False):
    if url[-1] != "/":
        url = url + "/"
    dir = "pages"
    try:
      os.mkdir(dir)
    except OSError, err:
        if err[0] != 17:
            raise
    nb_namespace = 16            
    for i in range(0,nb_namespace):    
        print "================== Import namespace %u/%u ============== " \
                % (i, nb_namespace-1)
        importNamespace(url, dir, i, only_last)

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
