def msdosDatetime(chunk):
    import datetime
    assert chunk.size == 4
    val = chunk.value
    sec = 2 * (val & 31)              # 5 bits: second
    min = (val >> 5) & 63             # 6 bits: minute
    hour = (val >> 11) & 31           # 5 bits: hour
    day = (val >> 16) & 31            # 5 bits: day
    month = (val >> 21) & 15          # 4 bits: month
    year = 1980 + ((val >> 25) & 127) # 7 bits: year
    return str(datetime.datetime(year, month, day, hour, min, sec))
    
def humanFilesize(chunk):
    from tools import humanFilesize as doHumanFilesize
    return doHumanFilesize(chunk.value)

def unixTimestamp(chunk):
    import datetime
    timestamp = datetime.datetime.fromtimestamp(chunk.value)
    return str(timestamp) 

def hexadecimal(chunk):
    size = chunk.size
    assert size in (2, 4, 8)
    pattern = "0x%0" + str(2*size) + "X"
    return pattern % chunk.value
