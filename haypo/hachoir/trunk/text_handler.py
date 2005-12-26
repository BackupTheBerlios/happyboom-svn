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
    pattern = "%0" + str(2*size) + "X"
    return pattern % chunk.value
