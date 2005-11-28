from filter import Filter
from plugin import registerPlugin
import re
from stream.error import StreamError
from tools import convertDataToPrintableString, getBacktrace
from stream.deflate import DeflateFilter
from error import warning

def isEnd(stream, array, last):
    return stream.eof()

def stripLine(chunk):
    return convertDataToPrintableString(chunk.value.strip())

class PdfObject(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pdf_obj", "PDF object", stream, parent)
        self.metadata = {}
        chunk = self.readString("header", "AutoLine", "Object header", post=stripLine)
        header = chunk.value 
        assert header != ""
        if header == "xref":
            self.type = "xref"
            self.readXref()
        else: 
            self.type = "obj"
            m = re.match(r"([0-9]+) [0-9]+ obj", header)
            if m != None:
                id = int(m.group(1))
                self.metadata["id"] = id
                self.setDescription("Object (id %s)" % id)
            else:
                self.metadata["id"] = header
                self.setDescription("Object (%s)" % header)
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
        self.setDescription("Object (%s)" % info)

    def readContent(self):
        text = "" 
        deflate = False
        while text not in ("endobj", "stream"):
            self.processLine(text)
            chunk = self.readString("line[]", "AutoLine", "", post=stripLine)
            text = chunk.value
            if re.match(r".*/Filter /FlateDecode.*", chunk.value) != None:
                deflate = True
            if self.getStream().eof():
                return "eof"
        if chunk.value == "endobj":
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
            start = self.getStream().tell()
            size = self._stream.searchLength("endstream", False)
            if size == -1:
                raise Exception("Delimiter \"%s\" not found for %s (%s)!" % (delimiter, id, description))

            if what=="deflate":
                try:
                    old = self.getStream().tell()
                    self.readChild("deflate", DeflateFilter, start, size)
                except:
                    warning("Error while decompressing data of an objet.")
                    self.getStream().seek(start)
                    self.read("data", "!%us" % size, "Data (compressed with deflate)")
            else:
                self.read("data", "!%us" % size, "Data")
            assert self.getStream().tell() == (start+size)
            
            self.readString("data_end[]", "AutoLine", "Data end")
            self.readString("endobj", "AutoLine", "Object end", post=stripLine)
        ver = self.getParent().version
        eol = self.getStream().read(1, seek=False)
        if eol in ("\n", "\r"):
            self.readString("emptyline", "AutoLine", "")

    def readXref(self):
        chunk = self.readString("xref_header", "AutoLine", "XRef header", post=stripLine)
        m = re.match(r"^[0-9]+ ([0-9]+)$", chunk.value)
        assert m != None
        nb_ref = int(m.group(1)) - 1
        n = 0
        while n<nb_ref:
            chunk = self.readString("ref[]", "AutoLine", "Reference", post=stripLine)
            n = n + 1
        self.readString("endobj", "AutoLine", "Object end", post=stripLine)

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

class PdfFile(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "id", "", stream, parent)
        self.readString("pdf_version", "AutoLine", "PDF version")
        m = re.match("^%PDF-([0-9]+)\.([0-9]+)$", self["pdf_version"])
        assert m != None
        self.version = ( int(m.group(1)), int(m.group(2)) )
        if self.version[0] == 1 and self.version[1] > 0:
            # PDF > 1.0
            self.readString("header", "AutoLine", "PDF header")
        self.nb_ref = None
        while not stream.eof():
            try:
                self.readChild("obj[]", PdfObject)
            except StreamError, err:
                return
            except Exception, err:
                print "Exception in PDF: %s" % err
                print getBacktrace()
                return

registerPlugin(PdfFile, "application/pdf")
