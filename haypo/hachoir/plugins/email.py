"""
Email parser

Author: Victor Stinner
"""

from filter import Filter, DeflateFilter
from plugin import registerPlugin, guessPlugin, getPluginByMime
from error import warning
from mime import splitMimes
from error import warning
from stream.base_64 import Base64Stream
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
            if chunk.length == 0: return
            line = chunk.value

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
                    warning("Can't parse email header: %s" % line)

            linenb = linenb + 1

    def __contains__(self, key):
        return key.lower() in self._dict

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
        readEmailContent(self, stream.createSub(), True)

class EmailBody(Filter):
    def __init__(self, stream, parent=None, in_multipart=True):
        Filter.__init__(self, "email_body", "Email body", stream, parent)
        linenb = 1 
        empty_line = 0
        while not stream.eof():
            id = "body[%u]" % linenb
            chunk = self.readString(id, "AutoLine", "Body text")
            if not in_multipart:
                if chunk.length == 0:
                    empty_line = empty_line + 1
                    if empty_line == 2:
                        break
                else:
                    empty_line = 0
            linenb = linenb + 1

def readEmailContent(self, stream, in_multipart):
    mime = getEmailMime(self)
    if re.match("^multipart/", mime[0]) != None:
        readMultipartEmail(self, stream, mime[1]["boundary"])
    else:
        readBody(self, stream, mime, in_multipart)

def readBody(self, stream, mime, in_multipart):
    # Read encoding
    header = self["header"]
    if "Content-Transfer-Encoding" in header:
        encoding = header["Content-Transfer-Encoding"][0]
    else:
        encoding = None

    # Get filename
    filename = mime[1].get("name", None)
    if filename == None:
        if "Content-Disposition" in header:
            disp = header["Content-Disposition"][0].split(";")
            regex = re.compile("filename=\"([^\"]+)\"")
            for item in disp:
                m = regex.match(item.strip())
                if m != None:
                    filename = m.group(1)
                    break
    elif filename[0] == '"':
        filename = filename[1:-1]

    # Handler base64 encodocing
    if encoding == "base64":
        size = stream.getSize() - stream.tell()
        data = stream.getN(size, False)
        substream = Base64Stream(data)
        deflate = True
    else:
        substream = stream
        deflate = False

    # Guess plugin
    plugin = getPluginByMime((mime,), None)
    if plugin == None:
        plugin = guessPlugin(substream, filename, None)
    if plugin == None:
        plugin = EmailBody

    # Finally read data
    if plugin != EmailBody:
        if deflate:
            self.readChild("body", DeflateFilter, substream, size, plugin) 
        else:
            chunk = self.readStreamChild("body", substream, plugin)
    else:
        if deflate:
            self.readChild("body", DeflateFilter, substream, size, plugin, in_multipart) 
        else:
            chunk = self.readStreamChild("body", substream, plugin, in_multipart)

def readMultipartEmail(self, stream, boundary):
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

def getEmailMime(self):
    content_type = self["header"]["Content-Type"]
    assert len(content_type) == 1
    mimes = splitMimes(content_type[0])
    assert len(mimes) == 1
    return mimes[0]

class Email(Filter):
    def __init__(self, stream, parent, in_multipart=True):
        Filter.__init__(self, "email", "Email", stream, parent)
        self.readString("id", "AutoLine", "Email identifier")
        self.readChild("header", EmailHeader)
        readEmailContent(self, stream.createSub(), in_multipart)

class EmailFilter(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "email", "Email maildir parser", stream, parent)
        cpt = 1
        while not stream.eof():
            chunk = self.readChild("email[%u]" % cpt, Email, False)
            end = stream.read(4, seek=False)
            if len(end.strip()) == 0:
                break
            cpt = cpt + 1

registerPlugin(EmailFilter, ["message/rfc822", "text/x-mail"])
