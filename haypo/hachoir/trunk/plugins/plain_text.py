"""
Plain text parser.

Author: Victor Stinner
"""

from filter import OnDemandFilter
from chunk import StringChunk
from plugin import registerPlugin
   
class PlainTextFile(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "plain", "Plain text file", stream, parent, "<")
        while not stream.eof():
            self.read("line[]", "Line", (StringChunk, "AutoLine"))

registerPlugin(PlainTextFile, "text/plain")
