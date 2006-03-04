import re, os
from stat import S_ISDIR, ST_MODE
from mime import getFileMime, getStreamMime
from error import warning

hachoir_parsers = {} 

regex_plugin_filename = re.compile(r"^([a-z0-9_]+)\.py$")

def loadParser(module_path, loaded):
    try:
        module = __import__(module_path)
        for get in module_path.split(".")[1:]:
            module = getattr(module, get)
    except Exception, msg:
        warning("Error while loading the plugin \"%s\": %s" \
            % (module_path, msg))
        return
    for attr in module.__dict__:
        item = getattr(module, attr)
        if hasattr(item, "mime_types"):
            registerParser(item, item.mime_types)
            loaded.append(module_path)

def loadParserPlugins(dir=None, module_path="libhachoir.parser", loaded=[]):
    """
    Load all plugings from directory dir. Don't give any argument, they are
    used internally.

    Returns a list of loaded plugins.
    """
    if dir == None:
        rootdir = os.path.dirname(__file__)
        dir = os.path.join(rootdir, "parser")
    if module_path == None:
        module_path = os.path.basename(dir)
    for file in os.listdir(dir):
        fullpath = os.path.join(dir, file)
        if S_ISDIR(os.stat(fullpath)[ST_MODE]):
            loadParserPlugins(fullpath, module_path+"."+file, loaded)
        else:
            m = regex_plugin_filename.match(file)
            if m != None and m.group(1) != "__init__":
                path = module_path + "." + m.group(1)
                loadParser(path, loaded)
    return loaded                    

def guessParser(stream, filename, default=None):
    return getParserByStream(stream, filename, default)

def getParserByMime(mimes, default=None):
    global hachoir_parsers
    plugins = []
    for mime in mimes:
        mime = mime[0]
        if mime in hachoir_parsers:
            for plugin in hachoir_parsers[mime]:
                if plugin not in plugins:
                    plugins.append(plugin)
    if len(plugins)==0:
        return default
    if 1<len(plugins):
        plist = []
        for plugin in plugins:
            plist.append(plugin.__name__)
        plist = ", ".join(plist)
        warning("More than one plugin have same MIME:\n%s" % plist)
    return plugins[0]
    
def getParserByStream(stream, filename, default=None):
    mime = getStreamMime(stream)
    return getParserByMime(mime, default)

def getParserByFile(filename, realname=None, default=None):
    mime = getFileMime(filename, realname)
    return getParserByMime(mime, default)
    
def registerParser(filter_class, mimes):
    global hachoir_parsers
    if isinstance(mimes, str):
        mimes = [mimes]
    for mime in mimes:
        if mime in hachoir_parsers:
            hachoir_parsers[mime].append(filter_class)
        else:
            hachoir_parsers[mime] = [filter_class]

