import re
from mime import getFileMime, getStreamMime
from default import DefaultFilter
from error import warning

def guessPlugin(stream, filename, default=DefaultFilter):
    return getPluginByStream(stream, filename, default)

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
    
def getPluginByStream(stream, filename, default=DefaultFilter):
    mime = getStreamMime(stream, filename)
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
