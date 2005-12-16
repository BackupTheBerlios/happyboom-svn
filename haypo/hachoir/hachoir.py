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
    print "\t--no-ui           : Don't load user interface"
    print "\t--use-profiler    : Use profiler"
    print "\t--version         : Show the program version"
    print "\t--verbose         : Activate verbose mode"
    print "\t--help            : Show this help"

def parseArgs(val):
    import getopt
    def_val = val.copy()
    
    try:
        short = ""
        long = ["verbose", "help", "version", "script=", "no-ui", "use-profiler"]
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
        elif o == "--version":
            print "%s version %s" % (PROGRAM, VERSION)
            sys.exit()
        elif o == "--no-ui":
            val["load_ui"] = False
        elif o == "--script":
            val["script"] = a
        elif o == "--verbose":
            val["verbose"] = True
        elif o == "--use-profiler":
            val["use_profiler"] = True
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
            "script": None,
            "load_ui": True,
            "use_profiler": False
        }
        opt, filename = parseArgs(opt)
        global hachoir 
        hachoir = Hachoir()
        for key in opt:
            setattr(hachoir, key, opt[key])
        if hachoir.load_ui:
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
        if opt["use_profiler"]:
            import profile, pstats
            stat_filename = 'hachoir.pystat'
            if filename != None:
                str_filename = "\"%s\"" % filename
            else:
                str_filename = "None"
            profile.run('global hachoir; hachoir.run(%s)' % str_filename, stat_filename)
            # .sort_stats('time')
            pstats.Stats(stat_filename).sort_stats('cumulative').print_stats()
            os.unlink(stat_filename)
        else:
            hachoir.run(filename)


    except SystemExit:
        pass
    except Exception, err:
        where = "".join(traceback.format_exception( \
            sys.exc_type, sys.exc_value, sys.exc_traceback))
        error("Exception:\n%s\n%s" % (err, where))
	sys.exit(1)

if __name__=="__main__": main()    
