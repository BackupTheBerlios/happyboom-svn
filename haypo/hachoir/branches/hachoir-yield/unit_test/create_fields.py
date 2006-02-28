from StringIO import StringIO
from field import FieldSet, Integer, String, Bits, Bit
from stream.file import FileStream
from bits import long2raw, str2hex

def test1():
    data = "\x02\x01abc\x09"
    stream = FileStream(StringIO(data), None)
    class TestInteger(FieldSet):
        def __init__(self, a, b, c):
            FieldSet.__init__(self, a, b, c)
            self.endian = ">"
        def createFields(self):
            yield Integer(self, "word", "uint16", "One integer")
            yield String(self, "abc", "string[3]", "abc string")
            yield Integer(self, "byte", "uint8", "Byte")
    test = TestInteger(None, "test", stream) 

    assert "word" in test
    field = test["word"]
    assert field.size == 16
    assert field.value == 0x0201

    assert "abc" in test
    field = test["abc"]
    assert field.address == 2*8
    assert field.size == 3*8
    assert field.value == "abc"

    assert "byte" in test
    field = test["byte"]
    assert field.address == 5*8
    assert field.size == 8
    assert field.value == 9

def test2():
    data = "\x21\x43" # concat(0x01, 0x23, 0x4)
    stream = FileStream(StringIO(data), None)
    class TestInteger(FieldSet):
        def createFields(self):
            yield Bits(self, "a", 4)
            yield Integer(self, "b", "uint8")
            yield Bits(self, "c", 4)
    test = TestInteger(None, "test", stream) 

    assert test["a"].value == 1
    assert test["b"].value == 0x32
    assert test["c"].value == 4 

def test2_str():
    data = "\x19\x46" # concat(0x09, 0x61, 0x4)
    
    stream = FileStream(StringIO(data), None)
    class TestInteger(FieldSet):
        def createFields(self):
            yield Bits(self, "a", 4)
            yield String(self, "b", "string[1]")
            yield Bits(self, "c", 4)
    test = TestInteger(None, "test", stream) 

    assert test["a"].value == 9
    assert test["b"].value == "a"
    assert test["c"].value == 4 

def test2_str2():
    data   = 1        ;  data <<= 4
    data  += 4        ;  data <<= 8
    data  += ord("a") ;  data <<= 2
    data  += 3
    data = long2raw(data, big_endian=False)
    
    stream = FileStream(StringIO(data), None)
    class TestInteger(FieldSet):
        def createFields(self):
            yield Bits(self, "a", 2)
            yield String(self, "b", "string[1]")
            yield Bits(self, "c", 4)
            yield Bits(self, "d", 2)
    test = TestInteger(None, "test", stream) 

    assert test["a"].value == 3
    assert test["b"].value == "a"
    assert test["c"].value == 4 
    assert test["d"].value == 1

def test3():
    data  = (1 & 0x1) << 0
    data += (3 & 0x7) << 1
    data += (0 & 0x3) << 4
    data += (2 & 0x3) << 6
    data = chr(data)
    stream = FileStream(StringIO(data), None)
    class TestInteger(FieldSet):
        def createFields(self):
            yield Bit(self, "a")
            yield Bits(self, "b", 3)
            yield Bits(self, "c", 2)
            yield Bits(self, "d", 2)
    test = TestInteger(None, "test", stream) 

    assert test["a"].value == True
    assert test["b"].value == 3
    assert test["c"].value == 0
    assert test["d"].value == 2

def runTests():
    print "Test FieldSet.createField()"
    try:
        test1()   
        test2()
        test2_str()
        test2_str2()
        test3()
        print "Test FieldSet.createField(): done"
    except Exception, msg: 
        print "Test FieldSet.createField(): error"
        print msg

