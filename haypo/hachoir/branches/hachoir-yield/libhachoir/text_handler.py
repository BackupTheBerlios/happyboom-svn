import datetime
from tools import humanFilesize as doHumanFilesize
from bits import str2bin

def msdosDatetime(chunk):
    assert chunk.size == 4
    val = chunk.value
    sec = 2 * (val & 31)              # 5 bits: second
    minute = (val >> 5) & 63          # 6 bits: minute
    hour = (val >> 11) & 31           # 5 bits: hour
    day = (val >> 16) & 31            # 5 bits: day of the month
    month = (val >> 21) & 15          # 4 bits: month
    year = 1980 + ((val >> 25) & 127) # 7 bits: year
    try:
        return str(datetime.datetime(year, month, day, hour, minute, sec))
    except:
        return "invalid msdos datetime (%s)" % val
    
def humanFilesize(chunk):
    return doHumanFilesize(chunk.value)

def unixTimestamp(field):
    timestamp = datetime.datetime.fromtimestamp(field.value)
    return str(timestamp) 

def binary(chunk):
    return str2bin(chunk.getRaw()) + " (%s)" % chunk.value

def hexadecimal(chunk):
    size = chunk.size
    assert size in (8, 16, 32, 64)
    pattern = "0x%0" + str(size/4) + "X"
    return pattern % chunk.value
