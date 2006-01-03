from filter import OnDemandFilter, DeflateFilter
from plugin import registerPlugin
from chunk import StringChunk, FormatChunk
import re
from stream.error import StreamError
from stream.deflate import DeflateStream
from tools import convertDataToPrintableString, getBacktrace
from error import warning
from default import DefaultFilter

def isEnd(stream, array, last):
    return stream.eof()

class PdfObject(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "obj", "object", stream, parent)
        self.metadata = {}
        header = self.doRead("header", "Object header", (StringChunk, "AutoLine"), {"strip": True}).value
        assert header != ""
        self.content = False
        if header == "xref":
            self.type = "xref"
            self.readXref()
        else: 
            self.type = "obj"
            m = re.match(r"([0-9]+) [0-9]+ obj", header)
            if m != None:
                id = int(m.group(1))
                self.metadata["id"] = id
                self.setDescription("Object: id %s" % id)
            else:
                self.metadata["id"] = header
                self.setDescription("Object: %s" % header)
            self.readObj()                
        self.updateDescription()

    def updateDescription(self):
        if self.type == "obj":
            info = "id %s" % self.metadata["id"]
            if "type" in self.metadata:
                info = info + ", %s" % self.metadata["type"]
                if "fontname" in self.metadata:
                    info = info + ", name: %s" % self.metadata["fontname"]
        else:
            info = "XREF"
        if self.content:
            info += " (content: %s)" % self.content
        self.setDescription("Object: %s" % info)

    def readContent(self):
        text = "" 
        deflate = False
        while text not in ("endobj", "stream"):
            self.processLine(text)
            chunk = self.doRead("line[]", "Line", (StringChunk, "AutoLine"), {"strip": True})
            text = chunk.value
            if re.match(r".*/Filter /FlateDecode.*", text) != None:
                deflate = True
            if self.getStream().eof():
                return "eof"
        if text == "endobj":
            chunk.id = "endobj"
            chunk.description = "Object end"
            return "end"
        elif deflate:
            return "deflate"
        else:
            return "stream"
    
    def readObj(self):
        what = self.readContent()
        if what == "eof":
            return
        if what in ("stream","deflate"):
            self.content = what
            start = self.getStream().tell()
            size = self._stream.searchLength("endstream", False)
            if size == -1:
                raise Exception("Delimiter \"%s\" not found for %s (%s)!" % (delimiter, id, description))

            if what=="deflate":
                try:
                    old = self.getStream().tell()
                    new_stream = DeflateStream( self.getStream().getN(size,False) )
                    self.read("content", "Deflate content", (DeflateFilter, new_stream, size, DefaultFilter))
                except:
                    warning("Error while decompressing data of an objet.")
                    self.getStream().seek(start)
                    self.read("data", "Data (compressed with deflate)", (FormatChunk, "string[%u]" % size))
            else:
                self.read("data", "Data", (FormatChunk, "string[%u]" % size))
            assert self.getStream().tell() == (start+size)
            
            self.read("data_end[]", "Data end", (StringChunk, "AutoLine"))
            self.read("endobj", "Object end", (StringChunk, "AutoLine"), {"strip": True})
        ver = self.getParent().version
        eol = self.getStream().read(1, seek=False)
        if eol in ("\n", "\r"):
            self.read("emptyline", "Empty line", (StringChunk, "AutoLine"))

    def readXref(self):
        text = self.doRead("xref_header", "XRef header", (StringChunk, "AutoLine"), {"strip": True}).value
        m = re.match(r"^[0-9]+ ([0-9]+)$", text)
        assert m != None
        nb_ref = int(m.group(1)) - 1
        n = 0
        while n<nb_ref:
            self.read("ref[]", "Reference", (StringChunk, "AutoLine"), {"strip": True})
            n = n + 1
        self.read("endobj", "Object end", (StringChunk, "AutoLine"), {"strip": True})

    def processLine(self, line):
        tests = {
            "type":  r"^.*Type /([A-Za-z]+)$",
            "fontname":  r"^.*(?:BaseFont|FontName) /(?:[A-Z]A+\+)?([A-Za-z-]+)$"
        }
        for field in tests:
            m = re.match(tests[field], line)
            if m != None:
                self.metadata[field] = m.group(1)
                break 

class PdfFile(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "id", "", stream, parent)
        self.read("pdf_version", "PDF version", (StringChunk, "AutoLine"))
        m = re.match("^%PDF-([0-9]+)\.([0-9]+)$", self["pdf_version"])
        assert m != None
        self.version = ( int(m.group(1)), int(m.group(2)) )
        if self.version[0] == 1 and self.version[1] > 0:
            # PDF > 1.0 (?)
            self.read("header", "PDF header", (StringChunk, "AutoLine"), {"charset": "utf-8"})
        self.nb_ref = None
        while not stream.eof():
            try:
                self.read("obj[]", "Object", (PdfObject,))
            except StreamError, err:
                return
            except Exception, err:
                print "Exception in PDF: %s" % err
                print getBacktrace()
                return

registerPlugin(PdfFile, "application/pdf")
