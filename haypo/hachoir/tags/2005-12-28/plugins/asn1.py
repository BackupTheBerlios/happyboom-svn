"""
(Very experimental) ASN1 Parser

Information: http://www.openssl.org/docs/apps/asn1parse.html

Author: Victor Stinner
"""

from filter import OnDemandFilter

class ASN1_Sequence(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "asn1_seq", "ASN1 sequence", stream, parent)
        while not stream.eof():
            self.read("item[]", "Item", (ASN1_Object,))

class ASN1_Object(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "asn1_obj", "ASN1 object", stream, parent)
        self.read("type", "type", (FormatChunk, "uint8"))
        tag = self.type & 0x1f
        if tag == 0x1f:
            raise Exception("Error in ASN1 parser: TODO ...")
        else:
            length = stream.getFormat("uint8", False)[0]
            if 128 <= length:
                size = length & 0x7f 
                length = 0
                oldpos = stream.tell()
                for i in range(0,size):
                    stream.seek(oldpos+1+i)
                    new = stream.getFormat("uint8", False)[0]
                    length = length * 256 + new
                    assert length < (1 << 32)
                stream.seek(oldpos)
                self.length = length
                self.read("dummylength", "Length", (FormatChunk, "string[%u]" % (1+size)))
            else:
                self.read("length", "Length", (FormatChunk, "uint8"))
            self.getChunk("type").description = "type (tag=%s)" % tag
            handler = {
                0: self.readEOC,
                1: self.readBoolean,
                4: self.readOctetString,
#                6: self.readObject,
                10: self.readEnum,
                12: self.readUTF8,
                16: self.readSequence
            }
            if tag in handler:
                handler[tag] ()
            else:
                self.read("value", "Value (don't know tag %s)" % tag, (FormatChunk, "string[%u]" % length))

    def readEnum(self):
        self.read("value", "Value (EOC)", (FormatChunk, "string[%u]" % self.length))

    def readObject(self):
        self.read("object", "Object", (ASN1_Object,))

    def readEOC(self):
        self.read("value", "Value (EOC)", (FormatChunk, "string[%u]" % self.length))

    def readOctetString(self):
        self.read("value", "Value (octet string)", (FormatChunk, "string[%u]" % self.length))

    def readBoolean(self):
        self.read("value", "Value (boolean)", (FormatChunk, "uint8"))

    def readUTF8(self):
        self.read("value", "Value (string)", (FormatChunk, "string[%u]" % self.length))
        
    def readSequence(self):
        self.readLimitedChild("sequence", self.length, ASN1_Sequence)

class ASN1_Parser(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "asn1", "ASN1 parser", stream, parent)
        self.read("object", "Ojbect", (ASN1_Object,))
