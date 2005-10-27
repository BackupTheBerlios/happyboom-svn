import re

def getPlugin(filename):
    global hachoir_plugins
    for plugin in hachoir_plugins:
        if plugin[0].match(filename) != None: return plugin
    return None
    
def registerPlugin(regex, name, splitFunc, displayFunc):
    global hachoir_plugins
    regex = re.compile(regex)
    hachoir_plugins.append( (regex, name, splitFunc, displayFunc,) )

hachoir_plugins = [] 
