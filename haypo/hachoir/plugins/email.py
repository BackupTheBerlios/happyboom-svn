"""
Email parser

Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin
from error import warning
from mime import splitMimes
import re

class EmailHeader(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "email_hdr", "Email header", stream, parent)
        self._dict = {}
        regex_new = re.compile("^([A-Za-z-]+): (.*)$")
        regex_continue = re.compile("^\t(.*)$")
        linenb = 1
        last_key = None
        last_index = None
        while True:
            id = "header[%u]" % linenb
            chunk = self.readString(id, "AutoLine", "Header line")
            line = chunk.value
            if len(line) == 0: return

            m = regex_new.match(line)
            if m != None:
                last_key = m.group(1)
                last_index = self._newHeader(last_key, m.group(2))
            else:
                m = regex_continue.match(line)
                if m != None:
                    assert last_key != None
                    self._appendHeader(last_key, last_index, m.group(1))
                else:
                    warning("Can't parse line %u: %s" % (linenb, line))

            linenb = linenb + 1

    def _appendHeader(self, key, index, value):
        key = key.lower()
        self._dict[key][index] = self._dict[key][index] + " " + value
        
    def _newHeader(self, key, value):
        key = key.lower()
        if key in self._dict:
            index = len(self._dict[key])
            self._dict[key].append(value)
        else:
            index = 0
            self._dict[key] = [value]
        return index

    def __getitem__(self, index):
        index = index.lower()
        return self._dict[index]

class EmailPart(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "email_part", "Email part", stream, parent)
        self.readChild("header", EmailHeader)
        linenb = 1 
        nb_empty_line = 0
        while not stream.eof():
            id = "header[%u]" % linenb
            chunk = self.readString(id, "AutoLine", "Header line")
            linenb = linenb + 1

class EmailFilter(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "email", "Email parser", stream, parent)
        self.readString("id", "AutoLine", "Email identifier")
        self.readChild("header", EmailHeader)
        mime = self.getMime()
        if mime[0] == "multipart/mixed":
            self.readMultipart(mime[1]["boundary"])
        else:
            # TODO :-)
            pass

    def readMultipart(self, boundary):
        assert boundary[0] == '"' and boundary[-1] == '"'
        boundary = "--" + boundary[1:-1]
        end_boundary = boundary + "--"
        count = 1
        while True:
            id = "multipart_space[%u]" % count
            chunk = self.readString(id, "AutoLine", "Space before first email parts")
            value = chunk.value
            if value == boundary:
                break
            count = count + 1

        part = 1
        boundary_index = 1
        stream = self.getStream()
        while True:
            start = stream.tell()
            size = stream.searchLength(boundary, False)
            sub = stream.createSub(start, size)
            self.readStreamChild("part[%u]" % part, sub, EmailPart)
            stream.seek(start+size)
            chunk = self.readString("boundary[%u]" % boundary_index, "AutoLine", "Boundary")
            part = part + 1
            boundary_index = boundary_index + 1
            if chunk.value == boundary+"--":
                break
    
    def getMime(self):
        content_type = self.header["Content-Type"]
        assert len(content_type) == 1
        mimes = splitMimes(content_type[0])
        assert len(mimes) == 1
        return mimes[0]

registerPlugin(EmailFilter, "text/x-mail")
