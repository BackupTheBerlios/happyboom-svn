from libhachoir.field import FieldSet, Integer, String, Bits, Bit
from libhachoir.stream import StringInputStream

def test1():
    stream = StringInputStream("\x00\x0A\x00\x0B\x05\x07")
    assert stream.searchBytes("\x0A", 0) == 8
    assert stream.searchBytes("\xFF", 0) == None
    assert stream.searchBytes("\x00", 8) == 16

def runTests():
    print "Test FieldSet.__getitem__"
    try:
        test1()
        print "Test FieldSet.__getitem__: done"
    except Exception, msg:
        print "Test FieldSet.__getitem__: error!"
        print msg
        raise
