import re
from mime import getFileMime, getBufferMime
from default import DefaultFilter

def guessPlugin(stream, filename):
    oldpos = stream.tell()
    size = stream.getSize()
    if 4096<size:
        size = 4096
    buffer = stream.getN(size)
    plugin = getPluginByBuffer(buffer, filename)
    stream.seek(oldpos)
    return plugin

def getPluginByMime(mimes):
    global hachoir_plugins
    plugins = []
    for mime in mimes:
        mime = mime[0]
        if mime in hachoir_plugins:
            plugins = plugins + hachoir_plugins[mime]
    if len(plugins)==0:
        plugins = (DefaultFilter,)
    if 1<len(plugins):
        warning("More than one plugin have same MIME...")
    return plugins[0]
    
def getPluginByBuffer(buffer, filename):
    mime = getBufferMime(buffer, filename)
    return getPluginByMime(mime)

def getPluginByStream(stream, filename):
    oldpos = stream.tell()
    stream.seek(0)
    size = stream.getSize()
    if 4096<size:
        size = 4096
    data = stream.getN(size)
    stream.seek(oldpos)
    mime = getBufferMime(data, filename)
    return getPluginByMime(mime)

def getPluginByFile(filename, realname=None):
    mime = getFileMime(filename, realname)
    return getPluginByMime(mime)
    
def registerPlugin(filter_class, mime):
    global hachoir_plugins
    if mime in hachoir_plugins:
        hachoir_plugins[mime].append(filter_class)
    else:
        hachoir_plugins[mime] = [filter_class]

hachoir_plugins = {} 
