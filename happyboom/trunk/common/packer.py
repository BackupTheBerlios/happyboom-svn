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

def packInt(data):
    assert checkType("int", data), "packInt argument have to be an integer"
    return struct.pack("!i", data)
    
def packUtf8(data):
    assert checkType("utf8", data), "packUtf8 argument have to be an unicode string"
    return packBin(data.encode("utf-8"))

def packBin(data):
    assert checkType("bin", data), "packBin argument have to be a string"
    return struct.pack("!H%us" % len(data), len(data), data)

def pack(func, event, types, values):
    """
    Pack arguments to binary string. Supported types :
    - "int": L{packInt}
    - "bin": L{packBin}
    - "utf8": L{packUtf8}
    """

    assert len(types) == len(values), "Lengths of types and args have to be the same."
    out = struct.pack("!BB", func, event)

    for i in range(len(values)):
        type = types[i]
        data = values[i]
        
        if type=="int":
            data = packInt(data)
        elif type=="bin":
            data = packBin(data)
        elif type=="utf8":
            data = packUtf8(data)
        else:
            raise PackerException("Wrong argument type: %s" % type)
        out = out + data
    return out        

def unpackBin(data):        
    fmt = "!H"
    i = struct.calcsize(fmt)
    version_len, = struct.unpack(fmt, data[:i])
    data = data[i:]
    fmt = "!%us" %(version_len)
    i = struct.calcsize(fmt)
    bin, = struct.unpack(fmt, data[:i])
    return bin, data[i:]

def unpackUtf8(data):
    str, data = unpackBin(data)
    str = unicode(str, "UTF-8")
    return str, data
 
def unpackInt(data):
    fmt = "!i"
    i = struct.calcsize(fmt)
    value = struct.unpack(fmt, data[:i])
    return value, data[i:]

def unpack(data, feature_id, event_id, protocol):
    """
    Unpack binary string to arguments.
    """
    feat = protocol.getFeatureById(feature_id)
    evt = feat.getEventById(event_id)
    args = []
    for type in evt.getParamTypes():
        if type=="int":
            arg, data = unpackInt(data)
        elif type=="bin":
            arg, data = unpackBin(data)
        else:
            raise PackerException("Wrong argument type: %s" % type)
        args.append(arg)
    return (feat.name, evt.name, args)
