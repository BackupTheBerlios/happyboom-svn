from libhachoir.field import FieldSet, Integer, String, Bits, Bit
from libhachoir.stream import StringInputStream

class Header(FieldSet):
    def createFields(self):
        yield Integer(self, "width", "int16", "Width") 
        yield Integer(self, "height", "int16", "Height") 

class Body(FieldSet):
    def createFields(self):
        yield Integer(self, "x", "uint8", "Item") 
        yield Integer(self, "y", "uint8", "Item") 

class Document(FieldSet):
    def createFields(self):
        yield Header(self, "header", self.stream)
        yield Body(self, "body", self.stream)

def test():
    stream = StringInputStream("\x00\x0A\x00\x0B\x05\x07")
    document = Document(None, "document", stream)
    
    # Test path starting with "/"
    assert "/body" in document
    assert "/header" in document
    assert id(document["/header"]) == id(document["header"])
    header = document["/header"]
    body = document["/body"]
    assert id(document["/header/width"]) == id(header["width"])

    # Test path starting with ".."
    assert ".." in header
    assert "../" in header
    assert id(header[".."]) == id(document)
    assert id(header["../header"]) == id(header)
    assert id(body["../header/width"]) == id(header["width"])

def runTests():
    print "Test FieldSet.__getitem__"
    try:
        test()
        print "Test FieldSet.__getitem__: done"
    except Exception, msg:
        print "Test FieldSet.__getitem__: error!"
        print msg
        raise
