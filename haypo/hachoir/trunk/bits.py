def str2hex(value):
    text = "(hex) "
    for character in value:
        if text != "":
            text += " "
        text += "%02X" % ord(character)
    return text

def countBits(value):
    """
    0 -> 0 bit
    1 -> 1 bit
    2 -> 2 bits
    4 -> 3 bits
    ...
    """
    bits = 0
    if value < 0:
        bits += 1
        value = -value
    while value >= 1:
        bits += 1
        value >>= 1
    return bits        

def byte2bin(x, reverse=True):
    text = ""
    for i in range(0,8):
        if reverse:
            mask = 1 << (7-i)
        else:
            mask = 1 << i
        if (x & mask) == mask:
            text += "1"
        else:
            text += "0"
    return text            

def long2bin(value, reverse=True):
    text = ""
    while (value != 0 or text == ""):
        if text != "":
            text += " "
        byte = value & 0xFF            
        text += byte2bin(byte, not reverse)
        value >>= 8
    return text        

def str2bin(value, reverse=False):
    text = ""
    for character in value:
        if text != "":
            text += " "
        byte = ord(character)
        text += byte2bin(byte, not reverse)
    return text

def reverseBits(x):
    y = 0
    for i in range(0,8):
        mask = (1 << i)
        if (x & mask) == mask:
            y |= (1 << (7-i))
    return y

def str2long(data, reverse_byte=False):
    """
    Convert a string into a number with big endian order.
    Eg. "\0\1\2" => 0x001020
    """
    shift = 0
    value = 0
    for character in data:
        byte = ord(character)
        if reverse_byte:
            byte = reverseBits(byte)
        value += (byte << shift) 
        shift += 8
    return value        
