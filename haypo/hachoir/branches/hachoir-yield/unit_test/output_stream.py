from libhachoir.stream import StringOutputStream
from libhachoir.bits import str2bin

def CONTENT(output):
    output.paddingToByte()
    string = output.string
    string.seek(0)
    return string.read()

def test1():
    output = StringOutputStream()
    output.writeBit(True)
    assert str2bin(CONTENT(output)) == "10000000"

def test2():
    output = StringOutputStream()
    output.writeBit(False)
    output.writeBits(8, 0xFF)
    assert str2bin(CONTENT(output)) == "01111111 10000000"

def test3():
    output = StringOutputStream(big_endian=False)
    output.writeBit(True)
    assert str2bin(CONTENT(output)) == "00000001"

def test4():
    output = StringOutputStream(big_endian=False)
    output.writeBit(False)
    output.writeBits(8, 0xFF)
    assert str2bin(CONTENT(output)) == "11111110 00000001"

def runTests():
    test1()
    test2()
    test3()
    test4()

