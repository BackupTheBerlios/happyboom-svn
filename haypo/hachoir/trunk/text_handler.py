from tools import humanFilesize as doHumanFilesize

def humanFilesize(chunk):
    return doHumanFilesize(chunk.value)

def hexadecimal(chunk):
    size = chunk.size
    assert size in (2, 4, 8)
    pattern = "%0" + str(2*size) + "X"
    return pattern % chunk.value
