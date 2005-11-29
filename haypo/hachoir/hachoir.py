#!/usr/bin/python
"""
Hachoir: tool to split a binary file into human readable data.
Because it's written in Python, it would be easy to write new plugins
(supports new file format).

Author: Victor Stinner
"""

import sys, os, re, traceback
from program import PROGRAM, VERSION, WEBSITE
from log import log
from error import error
from hachoir_class import Hachoir
import ui.ui as ui

def usage(defval):
    print "%s version %s" % (PROGRAM, VERSION)
    print "%s\n" % WEBSITE
    print "Usage: %s [options] file" % (sys.argv[0])
    print ""
    print "Options:"
    print "\t--script file.py  : Load python script"
    print "\t--version         : Show the program version"
    print "\t--verbose         : Activate verbose mode"
    print "\t--help            : Show this help"

def parseArgs(val):
    import getopt
    def_val = val.copy()
    
    try:
        short = ""
        long = ["verbose", "help", "version", "script="]
        opts, args = getopt.getopt(sys.argv[1:], short, long)
    except getopt.GetoptError:
        usage(def_val)
        sys.exit(2)
   
    if 1 < len(args):
        usage(def_val)
        sys.exit(2)
    if len(args) == 1:
        filename = args[0]
    else:
        filename = None
        
    for o, a in opts:
        if o == "--help":
            usage(def_val)
            sys.exit()
        if o == "--version":
            print "%s version %s" % (PROGRAM, VERSION)
            sys.exit()
        if o == "--script":
            val["script"] = a
        if o == "--verbose":
            val["verbose"] = True
    return (val, filename,)

def main():
    try:        
        print "%s version %s" % (PROGRAM, VERSION)
        print "%s\n" % WEBSITE
    
        import imp
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        plugins_files = os.listdir(plugins_dir)
        file_py = re.compile("^([a-z0-9_]+)\.py$")
        modules = []
        for file in plugins_files:
            m = file_py.match(file)
            if file != "__init__.py" and m != None:
                module = "plugins."+m.group(1)
                __import__(module)
                modules.append(m.group(1))
        log.info("Loaded: %u plugings (%s)" % (len(modules), ", ".join(modules)))

        opt = {
            "verbose": False,
            "script": None
        }
        opt, filename = parseArgs(opt)

        hachoir = Hachoir()
        for key in opt:
            setattr(hachoir, key, opt[key])
        try:
            ui.loadInterface(hachoir)
        except ImportError, err:
            error("""Error: a Python module is missing:
%s

You can find PyGTK at: http://www.pygtk.org/
and PyGlade at: http://glade.gnome.org/

Gentoo: emerge pytgtk
Debian: apt-get install python2.4-gtk python2.4-magic
Ubuntu: apt-get install python-gtk2 python-glade2""" % (err))
            sys.exit(1)
        hachoir.run(filename)

    except SystemExit:
        pass
    except Exception, err:
        where = "".join(traceback.format_exception( \
            sys.exc_type, sys.exc_value, sys.exc_traceback))
        error("Exception:\n%s\n%s" % (err, where))
	sys.exit(1)

if __name__=="__main__": main()    
