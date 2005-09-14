import types # maybe only used for assertions
import struct

class PackerException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

def packInt(data):
    assert type(data)==type(1), "packInt argument have to be an integer"
    # Overflow is checked by struct.pack
    #assert data <= 2147483647, "packInt argument is too big (%s)" % data
    #assert -2147483648 <= data, "packInt argument is too small (%s)" % data
    return struct.pack("!i", data)
    
def packUtf8(data):
    assert type(data)==types.unicode, "packUtf8 argument have to be Unicode"
    return packBin(data.encode("utf-8"))

def packBin(data):
    return struct.pack("!Hs", len(data), data)

def pack(func, event, args):
    """
    Pack arguments to binary string. Supported types :
    - "int": L{packInt}
    - "bin": L{packBin}
    - "utf8": L{packUtf8}
    """

    assert (len(args) % 2) == 0, "Arguments length have to be even"
    out = "%s:%s" % (func, event)

    #TODO: Fix this :-)
    for i in range(0,len(args)-1, 2):
        type = args[i]
        data = args[i+1]
        
        # TODO: Use dict instead of long if list
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
    return struct.unpack("!Hs", data)[1]
    
def unpackInt(data):
    return struct.pack("!i", data)[0]

def unpack(data):
    """
    Unpack binary string to arguments.
    """
    
