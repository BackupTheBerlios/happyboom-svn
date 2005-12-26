"""
ASN1 Parser

Information: http://www.openssl.org/docs/apps/asn1parse.html

Author: Victor Stinner
"""

from filter import Filter

class ASN1_Sequence(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "asn1_seq", "ASN1 sequence", stream, parent)
        self.readArray("item", ASN1_Object, "Items", self.checkEnd)

    def checkEnd(self, stream, array, last):        
        return stream.eof()

class ASN1_Object(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "asn1_obj", "ASN1 object", stream, parent)
        
        import sys
        sys.stdout.write("%s: " % stream.tell())
        
        self.read("type", "B", "type")
        tag = self.type & 0x1f
        if tag == 0x1f:
            raise Exception("Error in ASN1 parser: TODO ...")
        else:
            length = stream.getFormat("B", False)[0]
            if 128 <= length:
                size = length & 0x7f 
                length = 0
                oldpos = stream.tell()
                for i in range(0,size):
                    stream.seek(oldpos+1+i)
                    new = stream.getFormat("B", False)[0]
                    length = length * 256 + new
                    assert length < (1 << 32)
                stream.seek(oldpos)
                self.length = length
                self.read("dummylength", "%uB" % (1+size), "Length")
            else:
                self.read("length", "B", "Length")
            print "Length = %s" % self.length
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
                handler[tag]()
            else:
                self.read("value", "%us" % length, \
                    "Value (don't know tag %s)" % tag)

    def readEnum(self):
        self.read("value", "%us" % self.length, "Value (EOC)")

    def readObject(self):
        self.readChild("object", ASN1_Object)

    def readEOC(self):
        self.read("value", "%us" % self.length, "Value (EOC)")

    def readOctetString(self):
        self.read("value", "%us" % self.length, "Value (octet string)")

    def readBoolean(self):
        self.read("value", "B", "Value (boolean)")

    def readUTF8(self):
        self.read("value", "%us" % self.length, "Value (string)")
        
    def readSequence(self):
        self.readLimitedChild("sequence", self.length, ASN1_Sequence)

class ASN1_Parser(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "asn1", "ASN1 parser", stream, parent)
        #self.readArray("item", ASN1_Object, "Items", self.checkEnd)
        self.readChild("a", ASN1_Object)
#        self.readChild("b", ASN1_Object)

    def checkEnd(self, stream, array, last):        
        return stream.eof()
