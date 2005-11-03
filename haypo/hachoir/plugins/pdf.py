from filter import Filter
from plugin import registerPlugin
import re
from tools import convertDataToPrintableString

def isEnd(stream, array, last):
    return stream.eof()

def stripLine(chunk):
    return convertDataToPrintableString(chunk.value.strip())

class PdfObject(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "value", "", stream, parent)
        n = 0
        while not stream.eof():
            chunk = self.readString("line[]", "AutoLine", "", post=stripLine)
            if chunk.value.strip() == ">>":
                break
            n = n + 1

class PdfXref(Filter):
    def __init__(self, stream, parent, nb_items):
        Filter.__init__(self, "id", "", stream, parent)
        n = 0
        while n<nb_items and not stream.eof():
            chunk = self.readString("line[]", "AutoLine", "", post=stripLine)
            n = n + 1

class PdfFile(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "id", "", stream, parent)
        self.readString("version", "AutoLine", "PDF version")
        while not stream.eof():
            try:
                chunk = self.readString("line[]", "AutoLine", "", post=stripLine)
                value = chunk.value.strip()
                if re.match("^\<\<", value) != None:
                    self.readChild("data[]", PdfObject)
                elif value == "stream":
                    break
                else:
                    m = re.match("^[0-9]+ ([0-9]+)$", value)
                    if m != None:
                        nb_ref = int(m.group(1))
                        self.readChild("xref", PdfXref, nb_ref)
            except Exception, err:
                print "Exception: %s" % err
                break

registerPlugin("^.*\.(PDF|pdf)$", "PDF document file", PdfFile, None)
