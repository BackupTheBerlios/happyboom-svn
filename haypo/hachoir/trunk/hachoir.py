#!/usr/bin/env python
"""
Hachoir: tool to split a binary file into human readable data.
Because it's written in Python, it would be easy to write new plugins
(supports new file format).

Author: Victor Stinner
"""

import getopt, os, re, sys
import config
from program import PROGRAM, VERSION, WEBSITE
from log import log
from error import error, warning
from hachoir_class import Hachoir
import ui.ui as ui

def usage():
    """ Print Hachoir command line usage to stdout. """
    print "%s version %s" % (PROGRAM, VERSION)
    print "%s\n" % WEBSITE
    print "Usage: %s [options] file" % (sys.argv[0])
    print ""
    print "Options:"
    options = ( \
        ("script file.py", (
            "Load python script after loading file",
            "(if any specified)")),
        ("no-ui", "Don't load user interface"),
        ("use-profiler", "Use profiler"),
        ("version", "Show the program version"),
        ("verbose", "Activate verbose mode"),
        ("help", "Show this help"),
        ("debug", "Enable debug mode (eg. display backtrace)")
    )
    width = max([len(option[0]) for option in options])
    for opt in options:
        if isinstance(opt[1], tuple):
            print "   --%s : %s" % (opt[0].ljust(width), opt[1][0])
            for line in opt[1][1:]:
                print "   %s%s" % (" " * (width+5), line)
        else:
            print "   --%s : %s" % (opt[0].ljust(width), opt[1])

def parseArgs(val):
    """ Parse command line arguments using getopt module.
   
    @parameter val: Default values.
    @type: C{dict}
    @return: Final values
    @rtype: C{dict}
    """
    try:
        allowed = ( \
            "verbose", "help", "version", "debug",
            "script=", "no-ui", "use-profiler")
        opts, args = getopt.getopt(sys.argv[1:], "", allowed)
    except getopt.GetoptError:
        usage()
        sys.exit(2)
   
    if 1 < len(args):
        usage()
        sys.exit(2)
    if len(args) == 1:
        filename = args[0]
    else:
        filename = None
        
    for option, value in opts:
        if option == "--help":
            usage()
            sys.exit()
        elif option == "--version":
            print "%s version %s" % (PROGRAM, VERSION)
            sys.exit()
        elif option == "--no-ui":
            val["load_ui"] = False
        elif option == "--script":
            val["script"] = value
        elif option == "--verbose":
            config.verbose = True
        elif option == "--debug":
            config.debug = True
        elif option == "--use-profiler":
            val["use_profiler"] = True
    return (val, filename,)

def main():
    """ Main function of the program Hachoir: read command line
    arguments, instanciate the Hachoir class, load user interface,
    load plugins, and then run the Hachoir. """
    try:        
        # Welcome message
        print "%s version %s" % (PROGRAM, VERSION)
        print "%s\n" % WEBSITE

        # Check Python version (need 2.4 or greater)
        if sys.hexversion < 0x02040000:
            print "Fatal error: you need Python 2.4 or greater!"
            sys.exit(1)

        # Parse command line options
        opt = {
            "verbose": False,
            "script": None,
            "load_ui": True,
            "use_profiler": False
        }
        opt, filename = parseArgs(opt)

        # Instanciate the Hachoir
        global hachoir
        hachoir = Hachoir()
        for key in opt:
            setattr(hachoir, key, opt[key])

        # Load user interface (if needed)
        if hachoir.load_ui:
            try:
                print "Load user interface."
                ui.loadInterface(hachoir)
            except ImportError, err:
                error("""Error: a Python module is missing:
%s

You can find PyGTK at: http://www.pygtk.org/
and PyGlade at: http://glade.gnome.org/

Gentoo: emerge pytgtk
Debian: apt-get install python2.4-gtk python2.4-magic
Ubuntu: apt-get install python-gtk2 python-glade2
Mandriva: urpmi pygtk2.0-libglade-2.6.2-1mdk (or pygtk2.0-libglade?)""" % (err))
                sys.exit(1)
    
        # Load all plugins
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        plugins_files = os.listdir(plugins_dir)
        match_module_name = re.compile("^([a-z0-9_]+)\.py$")
        modules = []
        print "Load plugins."
        for file in plugins_files:
            module_name = match_module_name.match(file)
            if file != "__init__.py" and module_name != None:
                module = "plugins." + module_name.group(1)
                try:
                    __import__(module)
                    modules.append(module_name.group(1))
                except Exception, msg:
                    warning("Error while loading the plugin \"%s\": %s" % \
                        (module, msg))
        modules.sort()
        log.info("Loaded: %u plugings (%s)" % (len(modules), ", ".join(modules)))

        # Run the Hachoir
        if opt["use_profiler"]:
            import profile, pstats
            stat_filename = 'hachoir.pystat'
            if filename != None:
                str_filename = "\"%s\"" % filename
            else:
                str_filename = "None"
            code = 'global hachoir; hachoir.run(%s)' % str_filename
            profile.run(code, stat_filename)
            if False:
                sort_by = 'cumulative'
            else:
                sort_by = 'time'
            stats = pstats.Stats(stat_filename).sort_stats(sort_by)
            stats.print_stats()
            os.unlink(stat_filename)
        else:
            hachoir.run(filename)

    except SystemExit:
        pass
    except Exception, err:
        error("Python Exception: %s" % err)
    sys.exit(1)

if __name__ == "__main__":
    main()
