#!/usr/bin/python
"""
Splitter: tool to split a binary file into human readable data.
Because it's written in Python, it would be easy to write new plugins
(supports new file format).

Author: Victor Stinner
"""

PROGRAM="Hachoir"
VERSION="2005-10-27"

import sys, os, re, traceback
from stream import FileStream
from plugin import getPlugin
from chunk import FilterChunk

def usage(defval):
    print "%s version %s" % (PROGRAM, VERSION)
    print ""
    print "Usage: %s [options] file" % (sys.argv[0])
    print ""
    print "Options:"
    print "\t--help            : Show this help"
    print "\t--version         : Show the program version"
    print "\t--verbose         : Activate verbose mode"
    print "\t--depth NB        : Detail depth (default %u)" % (defval["depth"])
    print "\t--no-display      : Hide result"

def parseArgs(val):
    import getopt
    def_val = val.copy()
    
    try:
        short = ""
        long = ["no-display", "verbose", "help", "version", "depth="]
        opts, args = getopt.getopt(sys.argv[1:], short, long)
    except getopt.GetoptError:
        usage(def_val)
        sys.exit(2)
   
    if len(args) != 1:
        usage(def_val)
        sys.exit(2)
        
    for o, a in opts:
        if o == "--help":
            usage(def_val)
            sys.exit()
        if o == "--version":
            print "%s version %s" % (PROGRAM, VERSION)
            sys.exit()
        if o == "--no-display":
            val["display"] = False
        if o == "--depth":
            val["depth"] = int(a)
        if o == "--verbose":
            val["verbose"] = True
    return (val, args[0],)

class Hachoir:
    def __init__(self):
        self.verbose = False
        self.display = True
        self.depth = 5

    def onGoParent(self):
        if self.filter.getParent() == None: return
        self.filter = self.filter.getParent()
        self.filter.display()
        
    def onRowClick(self, chunk_id):
        if chunk_id == None: return
        m = re.compile(r"^([^[]+)\[([0-9]+)\]$").match(chunk_id)
        if m != None:
            array = self.filter.getChunk(m.group(1))
            chunk = array[int(m.group(2))]
        else:
            chunk = self.filter.getChunk(chunk_id)
        if issubclass(chunk.__class__, FilterChunk):
            self.filter = chunk.getFilter()
            self.filter.display()

    def run(self, filename):
        import filter
        # Look for a plugin
        plugin = getPlugin(filename)
        if plugin != None:
            regex, plugin_name, split_func, display_func = plugin
            if self.verbose:
                print "Split file \"%s\": %s." % (filename, plugin_name)
            
            # Create stream
            stream = FileStream(filename)

            # Split 
            filter.display_filter_actions = self.depth
            if 0 < self.depth:
                print "=== Split file %s ===" % filename
            self.filter = split_func(stream)
            if 0 < self.depth:
                print ""
            self.filter.display()

            # Display
            if self.display:
                print "=== File %s data ===" % filename
                display_func(self.filter)
        else:
            print "No suitable plugin for \"%s\"." % (filename)
            sys.exit(1)

def main():
    try:        
        import imp
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        plugins_files = os.listdir(plugins_dir)
        file_py = re.compile("^([a-z0-9_]+)\.py$")
        modules = []
        for file in plugins_files:
            m = file_py.match(file)
            if m != None:
                module = "plugins."+m.group(1)
                __import__(module)
                modules.append(m.group(1))
        print "Loaded: %u plugings (%s)" % (len(modules), ", ".join(modules))

        opt = {
            "depth": 2,
            "verbose": False,
            "display": True
        }
        if len(sys.argv) < 2:
            usage(opt)
            sys.exit(1)

        opt, filename = parseArgs(opt)

        hachoir = Hachoir()
        for key in opt:
            setattr(hachoir, key, opt[key])

        try:
            import ui 
        except ImportError, err:
            print """Error: a Python module is missing:\n%s\n
You can find PyGTK at: http://www.pygtk.org/
and PyGlade at: http://glade.gnome.org/""" % (err)
            sys.exit(1)
        ui.loadInterface()
        ui.ui.on_row_click = hachoir.onRowClick
        ui.ui.on_go_parent = hachoir.onGoParent
        hachoir.run(filename)
        ui.ui.run()

    except SystemExit:
        pass
    except Exception, err:
        print "Exception:\n%s" % (err)
        print "".join(traceback.format_exception( \
            sys.exc_type, sys.exc_value, sys.exc_traceback))

if __name__=="__main__": main()    
