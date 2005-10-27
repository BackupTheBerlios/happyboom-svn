"""
Ncftp bookmarks filter.

Status: Read most import fields.
Author: Victor Stinner
"""

import re, base64
from filter import Filter
from plugin import registerPlugin
from stream import LimitedFileStream

def displayNcftp(data):
    print "Ncftp saved bookmarks:"
    for b in data.bookmarks:
        print "o %s (port %s): u=%s, p=\"%s\"" % \
            (b.server, b.port, b.username, b.password)

class NcftpBookmark(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.readField("name", "Bookmark name", ",")
        self.readField("server", "Server name/ip", ",")
        self.readField("username", "Username", ",")
        self.readField("password", "Password", ",")
        self.readField("notused1", "Not used (1)", ",")
        self.readField("last_dir", "Last directory", ",")
        self.readField("notused3", "Not used (3)", ",")
        self.readField("port", "Server port", ",")
        self.readLine("eol", "End of line", "\n")
        self.password = self.crackPass(self.password)
        
    def crackPass(self, password):
        m = re.compile("^\*encoded\*(.*)$").match(password)
        if m == None: return password
        password = base64.decodestring(m.group(1))
        return password.strip("\0")

class NcftpFilter(Filter):
    def __init__(self, stream):
        Filter.__init__(self, stream)
        self.readLine("header", "Header (first line")
        self.readLine("nb_bookmark", "Number of bookmarks")

        self.openChild()
        self.bookmarks = []
        while not self.stream.eof():
            self.newChild("Bookmark")
            self.bookmarks.append( NcftpBookmark(stream,self) )
        self.closeChild("Bookmarks")
        
registerPlugin("^.*bookmarks$", "NcFTP bookmarks", NcftpFilter, displayNcftp)
