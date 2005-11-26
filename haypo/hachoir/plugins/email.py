"""
Email parser

Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

class EmailFilter(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "email", "Email parser", stream, parent)
        print "OK"
        id = "header"
        ok = True
        while ok:
            id = self.getUniqChunkId(id)
            chunk = self.readString(id, "AutoLine", "Header line")
            print "+ %s" % chunk.value
            ok = (0 < len(chunk.value))

#    def checkEnd(self, stream, array, last):        
#        return stream.eof()

registerPlugin(EmailFilter, "text/x-mail")
