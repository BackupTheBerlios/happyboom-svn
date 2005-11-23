import re
from mime import getFileMime, getBufferMime

def guessPlugin(stream):
    oldpos = stream.tell()
    buffer = stream.getN(4096)
    plugin = getPluginByBuffer(buffer)
    stream.seek(oldpos)
    return plugin

def getPluginByMime(mime):
    global hachoir_plugins
    mime = mime[0]
    if mime not in hachoir_plugins:
        return None
    plugins = hachoir_plugins[mime]
    if 1<len(plugins):
        warning("More than one plugin have same MIME...")
    return plugins[0]       
    
def getPluginByBuffer(buffer):
    mime = getBufferMime(buffer)
    return getPluginByMime(mime)

def getPluginByStream(stream):
    stream.seek(0)
    data = stream.getN(4096)
    mime = getBufferMime(data)
    return getPluginByMime(mime)

def getPluginByFile(filename):
    mime = getFileMime(filename)
    return getPluginByMime(mime)
    
def registerPlugin(filter_class, mime):
    global hachoir_plugins
    if mime in hachoir_plugins:
        hachoir_plugins[mime].append(filter_class)
    else:
        hachoir_plugins[mime] = [filter_class]

hachoir_plugins = {} 
