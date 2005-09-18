import types # maybe only used for assertions
import struct

class PackerException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

def checkType(datatype, data):
    if datatype=="int":
        return (type(data) == type(1)) and (data <= 2147483647) and (-2147483648 <= data)
    elif datatype=="bin":
        return type(data)==types.StringType and len(data) < 65535 
    elif datatype=="utf8":
        return type(data)==types.UnicodeType and len(data) < 65535
    else:
        raise PackerException("Wrong argument type: %s" % datatype)

# Integer type
def packInt(data):
    assert checkType("int", data), "packInt argument have to be an integer"
    return struct.pack("!i", data)
    
def unpackInt(data):
    fmt = "!i"
    i = struct.calcsize(fmt)
    value, = struct.unpack(fmt, data[:i])
    return value, data[i:]
    
# unicode string type (encoded in UTF-8)
def packUtf8(data):
    assert checkType("utf8", data), "packUtf8 argument have to be an unicode string"
    return packBin(data.encode("utf-8"))

def unpackUtf8(data):
    str, data = unpackBin(data)
    str = unicode(str, "UTF-8")
    return str, data

# Binary string type
def packBin(data):
    assert checkType("bin", data), "packBin argument have to be a string"
    # TODO : verify length
    return struct.pack("!H%us" % len(data), len(data), data)

def unpackBin(data):        
    fmt = "!H"
    i = struct.calcsize(fmt)
    version_len, = struct.unpack(fmt, data[:i])
    data = data[i:]
    fmt = "!%us" %(version_len)
    i = struct.calcsize(fmt)
    bin, = struct.unpack(fmt, data[:i])
    return bin, data[i:]
