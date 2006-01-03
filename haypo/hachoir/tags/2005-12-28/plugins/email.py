"""
Email parser

Author: Victor Stinner
"""

from filter import OnDemandFilter, DeflateFilter
from plugin import registerPlugin, guessPlugin, getPluginByMime
from chunk import StringChunk
from default import DefaultFilter
from mime import splitMimes
from error import warning, error
from stream.base_64 import Base64Stream
import re

class EmailHeader(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "email_hdr", "Email header", stream, parent)
        self._dict = {}
        regex_new = re.compile("^([A-Za-z][A-Za-z0-9-]*): (.*)$")
        regex_continue = re.compile("^[\t ]+(.*)$")
        linenb = 1
        last_key = None
        last_index = None
        while True:
            id = "header[%u]" % linenb
            chunk = self.doRead(id, "Header line", (StringChunk, "AutoLine"))
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
        key = key.lower()
        return key in self._dict

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

class EmailPart(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "email_part", "Email part", stream, parent)
        self.read("header", "Header", (EmailHeader,))
        readEmailContent(self, stream.createSub())

class EmailBody(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "email_body", "Email body", stream, parent)
        linenb = 1 
        while not stream.eof():
            guess = stream.read(5, False)
            if guess=="From ":
                break
            id = "body[%u]" % linenb
            self.read(id, "Body text", (StringChunk, "AutoLine"))
            linenb = linenb + 1

def readEmailContent(self, stream):
    mime = getEmailMime(self)
    if mime != None and re.match("^multipart/", mime[0]) != None:
        readMultipartEmail(self, stream, mime[1]["boundary"])
    else:
        if mime == None:
            warning("Can't get MIME type for email %s" % self)
        readBody(self, stream, mime)

def readBody(self, stream, mime):
    # Read encoding
    header = self["header"]
    if "Content-Transfer-Encoding" in header:
        encoding = header["Content-Transfer-Encoding"][0]
    else:
        encoding = None

    # Get filename
    if mime != None:
        filename = mime[1].get("name", None)
    else:
        raise Exception("No MIME in readBody()")
        filename = None
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
#        regex_new_mail = re.compile("[\r\n]From ")
#        pos = stream.search(regex_new_mail)
#        if pos != -1:
#            substream = stream.createSub(size=pos)
#        else:
#            substream = stream
        substream = stream.createSub()
        deflate = False

    # Guess plugin
    if mime != None:
        plugin = getPluginByMime((mime,), None)
    else:
        plugin = None
    if plugin == None:
        plugin = guessPlugin(substream, filename, None)
    if plugin == None or plugin == EmailFilter:
        plugin = EmailBody

    # Finally read data
    try:
        if deflate:
            self.read("body", "Body", (DeflateFilter, substream, size, plugin))
        else:
            self.read("body", "Body", (plugin,), {"stream": substream})
    except Exception, msg:
        error("Error while parsing email body: %s" % msg)
        substream.seek(0)
        self.read("body", "Body", (DefaultFilter,), {"stream": substream})

def readMultipartEmail(self, stream, boundary):
    assert boundary[0] == '"' and boundary[-1] == '"'
    boundary = "--" + boundary[1:-1]
    end_boundary = boundary + "--"
    count = 1
    while True:
        id = "multipart_space[%u]" % count
        line = self.doRead(id, "Space before first email parts", (StringChunk, "AutoLine")).value
        if line == boundary:
            break
        count = count + 1

    part = 1
    boundary_index = 1
    while True:
        start = stream.tell()
        size = stream.searchLength(boundary, False)
        sub = stream.createSub(start, size)
        self.read("part[%u]" % part, "Email part %u" % part, (EmailPart,), {"stream": sub})
        stream.seek(start+size)
        line = self.doRead("boundary[%u]" % boundary_index, "Boundary", (StringChunk, "AutoLine")).value
        part = part + 1
        boundary_index = boundary_index + 1
        if line == boundary+"--":
            break

def getEmailMime(self):
    header = self["header"]
    if not("Content-Type" in header):
        raise Exception("No mime")
        return None
    content_type = header["Content-Type"]
    assert len(content_type) == 1
    mimes = splitMimes(content_type[0])
    assert len(mimes) == 1
    return mimes[0]

class Email(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "email", "Email", stream, parent)
        self.read("id", "Email identifier", (StringChunk, "AutoLine"))
        self.read("header", "Header", (EmailHeader,))
        #readEmailContent(self, stream.createSub())
        readEmailContent(self, stream)

    def __str__(self):
        header = self["header"]
        text = "Email"
        if "From" in header:
            text = text + " from %s" % header["From"]
        if "Date" in header:
            text = text + " (date %s)" % header["Date"]
        return text

class EmailFilter(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "email", "Email maildir parser", stream, parent)
        while not stream.eof():
            id = self.read("email[]", "Email", (Email,))
            if id == "email[2]": break

            # Search next email (line which starts with "From ")                
            while not stream.eof():
                guess = stream.read(5, False)
                if guess == "From ":
                    break
                self.read("space[]", "Space", (StringChunk, "AutoLine"))

registerPlugin(EmailFilter, ["message/rfc822", "text/x-mail"])
