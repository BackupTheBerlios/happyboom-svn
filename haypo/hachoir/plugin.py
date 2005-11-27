import re
from mime import getFileMime, getBufferMime
from default import DefaultFilter

def guessPlugin(stream, filename, default=DefaultFilter):
    oldpos = stream.tell()
    size = stream.getSize()
    if 4096<size:
        size = 4096
    buffer = stream.getN(size)
    plugin = getPluginByBuffer(buffer, filename, default)
    stream.seek(oldpos)
    return plugin

def getPluginByMime(mimes, default=DefaultFilter):
    global hachoir_plugins
    plugins = []
    for mime in mimes:
        mime = mime[0]
        if mime in hachoir_plugins:
            plugins = plugins + hachoir_plugins[mime]
    if len(plugins)==0:
        return default
    if 1<len(plugins):
        warning("More than one plugin have same MIME...")
    return plugins[0]
    
def getPluginByBuffer(buffer, filename, default=DefaultFilter):
    mime = getBufferMime(buffer, filename)
    return getPluginByMime(mime, default)

def getPluginByStream(stream, filename, default=DefaultFilter):
    oldpos = stream.tell()
    stream.seek(0)
    size = stream.getSize()
    if 4096<size:
        size = 4096
    data = stream.getN(size)
    stream.seek(oldpos)
    mime = getBufferMime(data, filename)
    return getPluginByMime(mime, default)

def getPluginByFile(filename, realname=None, default=DefaultFilter):
    mime = getFileMime(filename, realname)
    return getPluginByMime(mime, default)
    
def registerPlugin(filter_class, mimes):
    global hachoir_plugins
    if isinstance(mimes, str):
        mimes = [mimes]
    for mime in mimes:
        if mime in hachoir_plugins:
            hachoir_plugins[mime].append(filter_class)
        else:
            hachoir_plugins[mime] = [filter_class]

hachoir_plugins = {} 
