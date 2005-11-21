#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import sys, os, re, types
#from elementtree.ElementTree import ElementTree
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

def error(msg):
    print msg

def warning(msg):
    print msg

class Importer:
    def __init__(self, base_url):
        # Add "/" prefix to url if needed
        if base_url[-1] != "/":
            self.base_url = base_url+"/"
        else:
            self.base_url = base_url

        self.only_last = False
        self.dir = "pages"
        self.use_gzip = True
        self.max_per_file = 200 
        
    def download(self, page, params={}):
        params = urllib.urlencode(params)
        f = urllib.urlopen(self.base_url+page, params)
        return f.read()

    def getAllpages(self, namespace):
        pages = self.download("Special:Allpages", {"namespace": namespace})
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

    def savePages(self, namespace, part, content):
        if part != None:
            filename = "namespace_%s_part%u.xml" % (namespace, part)
        else:
            filename = "namespace_%s.xml" % namespace
        filename = os.path.join(self.dir, filename)
        if self.use_gzip:
            filename = filename + ".gz"
            f = GzipFile(filename, 'w')
            f.write(content)
            f.close()
        else:
            f = open(filename, 'w')
            f.write(content)
            f.close()
        print "saved to %s" % (filename)

    def importPages(self, namespace, pages, part):
        args = { \
            "action": "submit",
            "pages": "\n".join(pages)
        }
        if self.only_last:
            args["curonly"] = "on"
        data = self.download("Special:Export", args)
        if data == None:
            error("Fail to download namespace %s." % namespace)
            sys.exit(1)
        self.savePages(namespace, part, data)

    def importNamespace(self,  namespace):
        print "Download document list."
        pages = self.getAllpages(namespace)
        if pages == None:
            print "Error: Can't get document list."
            sys.exit(1)
        if len(pages) == 0:
            print "(empty)"
            return
        part = 1
        position = 1
        total = len(pages)
        while len(pages) != 0:
            if self.max_per_file != 0:
                sub = pages[:self.max_per_file]
                pages = pages[self.max_per_file:]
            else:
                sub = pages
                pages = []
            sys.stdout.write("Download document(s) %u..%u / %u ... " \
                 % (position, position+len(sub)-1, total))
            sys.stdout.flush()
            try:
                if total != len(sub):
                    self.importPages(namespace, sub, part)
                    part = part + 1
                    position = position + len(sub)
                else:
                    part = None
                    self.importPages(namespace, sub, part)
            except:
                sys.stdout.write("ERROR!\n\n")
                raise

    def doImport(self):
        # Which namespaces have to be downloaded?
        namespaces = range(0,16)
        namespaces.remove(8) # MediaWiki
        namespaces.remove(9) # Talk:MediaWiki

        # Sum up before starting
        print "Base url: %s" % (self.base_url)
        print "Store into gzip: %s" % (self.use_gzip)
        print "Max documents/file: %s" % (self.max_per_file)

        # Create pages/ if needed
        if not os.access(self.dir, os.F_OK):
            print "Create subdirectory %s" % (self.dir)
            os.mkdir(self.dir)
        print ""
        
        # Download each namespace
        i = 1
        for namespace in namespaces: 
            namespace = 6
            print "================== Import namespace %u (%u/%u) ============== " \
                    % (namespace, i, len(namespaces))
            self.importNamespace(namespace)
            return
            i = i + 1

if len(sys.argv) != 2:
    usage()
base_url = sys.argv[1]
try:
    from gzip import GzipFile
    use_gzip = True
except ImportError:
    warning("Can't load gzip module.")
    use_gzip = False
try:
    my = Importer(base_url)
    my.use_gzip = use_gzip
    my.doImport()
except KeyboardInterrupt:
    print "Interrupted (CTRL+C): be carefull, download incomplete!"
    sys.exit(1)
print ""    
