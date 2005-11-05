from filter import Filter
from plugin import registerPlugin
import re
from stream import StreamError
from tools import convertDataToPrintableString, getBacktrace

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
            m = re.match("([0-9]+) [0-9]+ obj", header)
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

    def readObj(self):
        chunk = self.readString("line[]", "AutoLine", "", post=stripLine)
        if re.match("^\<\<", chunk.value) != None:
            self.processLine(chunk.value)
            while re.match("^.*\>\>$", chunk.value) == None:
                chunk = self.readString("line[]", "AutoLine", "", post=stripLine)
                self.processLine(chunk.value)
        chunk = self.readString("endobj", "AutoLine", "Object end", post=stripLine)
        if chunk.value == "stream":
            chunk.id = "xref"
            lg = self._stream.searchLength("endstream", False)
            if lg == -1:
                raise Exception("Delimiter \"%s\" not found for %s (%s)!" % (delimiter, id, description))
            self.read("data[]", "!%us" % lg, "Data")
            self.readString("data_end[]", "AutoLine", "Data end")
            self.readString("endobj", "AutoLine", "Object end", post=stripLine)
        self.readString("emptyline", "AutoLine", "")

    def readXref(self):
        chunk = self.readString("xref_header", "AutoLine", "XRef header", post=stripLine)
        m = re.match("^[0-9]+ ([0-9]+)$", chunk.value)
        assert m != None
        nb_ref = int(m.group(1)) - 1
        n = 0
        while n<nb_ref:
            chunk = self.readString("ref[]", "AutoLine", "Reference", post=stripLine)
            n = n + 1
        self.readString("endobj", "AutoLine", "Object end", post=stripLine)

    def processLine(self, line):
        tests = {
            "type":  "^.*/Type /([A-Za-z]+)$",
            "fontname":  "^.*/FontName /[BD]A+\+([A-Za-z-]+)$"
        }
        for field in tests:
            m = re.match(tests[field], line)
            if m != None:
                self.metadata[field] = m.group(1)
                break 

class PdfFile(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "id", "", stream, parent)
        self.readString("version", "AutoLine", "PDF version")
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

registerPlugin("^.*\.(PDF|pdf)$", "PDF document file", PdfFile, None)
