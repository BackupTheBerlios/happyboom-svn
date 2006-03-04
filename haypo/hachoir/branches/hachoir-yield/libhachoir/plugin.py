import re, os
from stat import S_ISDIR, ST_MODE
from mime import getFileMime, getStreamMime
from error import warning

regex_plugin_filename = re.compile(r"^([a-z0-9_]+)\.py$")

def loadPluginFromFile(module_path, loaded):
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
            registerPlugin(item, item.mime_types)
            loaded.append(module_path)

def loadPlugins(dir, module_path="libhachoir.parser", loaded=[]):
    """
    Load all plugings from directory dir.

    Do not set module_path or loaded, they are used internally.
    """
    if module_path == None:
        module_path = os.path.basename(dir)
    for file in os.listdir(dir):
        fullpath = os.path.join(dir, file)
        if S_ISDIR(os.stat(fullpath)[ST_MODE]):
            loadPlugins(fullpath, module_path+"."+file, loaded)
        else:
            m = regex_plugin_filename.match(file)
            if m != None and m.group(1) != "__init__":
                path = module_path + "." + m.group(1)
                loadPluginFromFile(path, loaded)
    return loaded                    

def guessPlugin(stream, filename, default=None):
    return getPluginByStream(stream, filename, default)

def getPluginByMime(mimes, default=None):
    global hachoir_plugins
    plugins = []
    for mime in mimes:
        mime = mime[0]
        if mime in hachoir_plugins:
            for plugin in hachoir_plugins[mime]:
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
    
def getPluginByStream(stream, filename, default=None):
    mime = getStreamMime(stream, filename)
    return getPluginByMime(mime, default)

def getPluginByFile(filename, realname=None, default=None):
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
