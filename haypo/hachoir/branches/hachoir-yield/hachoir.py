#!/usr/bin/env python

VERSION = "0.2veryalpha"

import sys, os, getopt

cmd_line_options = ( \
    ("verbose", "Activate verbose mode"),
    ("help", "Show this help"),
    ("quiet", "Be quiet (don't display warning)"),
    ("version", "Display version"),
    ("debug", "Enable debug mode (eg. display backtrace)")
)

def usage():
#    global command_line_options
    print "Hachoir version %s" % VERSION
    print "Usage: %s [options] filename" % sys.argv[0]
    print
    width = max([len(option[0]) for option in cmd_line_options])
    for opt in cmd_line_options:
        if isinstance(opt[1], tuple):
            print "   --%s : %s" % (opt[0].ljust(width), opt[1][0])
            for line in opt[1][1:]:
                print "   %s%s" % (" " * (width+5), line)
        else:
            print "   --%s : %s" % (opt[0].ljust(width), opt[1])

def parseArgs():
    import libhachoir.config as config

    try:
        allowed = [ option[0] for option in cmd_line_options ]
        opts, args = getopt.getopt(sys.argv[1:], "", allowed)
    except getopt.GetoptError:
        usage()
        sys.exit(2)
   
    if len(args) != 1:
        usage()
        sys.exit(2)
    filename = args[0]
        
    for option, value in opts:
        if option == "--help":
            usage()
            sys.exit(0)
        elif option == "--version":
            print "Hachoir version %s" % VERSION
            sys.exit(0)
        elif option == "--quiet":
            config.quiet = True
        elif option == "--verbose":
            config.verbose = True
        elif option == "--debug":
            config.debug = True
    return filename 

def main():
    # Get libhachoir directory
    libhachoir_path = os.path.join(os.getcwd(), "libhachoir")
    sys.path.append(libhachoir_path)
    
    # Parser command line arguments
    filename = parseArgs()

    # Get tools that we need from libhachoir
    from libhachoir.stream import InputStream
    from text_ui import displayFieldSet
    from libhachoir.plugin import loadParserPlugins, guessParser
    from libhachoir.log import log
    from libhachoir.error import error
    from libhachoir.mime import getStreamMime
    from metadata import createMetaData
    import libhachoir.config as config

    # Create input stream (read filename from command line first argument)
    stream = InputStream(open(filename, 'r'), filename)

    # Load all parser plugings from 'file' directory
    root_dir = libhachoir_path
    modules = loadParserPlugins()
    if config.verbose:
        modules.sort()
        log.info("Loaded: %u plugings (%s)" % (len(modules), ", ".join(modules)))

    # Look for right plugin
    plugin = guessParser(stream, filename, None)
    if plugin == None:
        msg  = "Sorry, can't find plugin for file \"%s\"!" % filename
        mimes = [ mime[0] for mime in getStreamMime(stream) ]
        msg += "\n\nFile mimes: %s" % ", ".join(mimes)
        error(msg)
        sys.exit(1)

    # Create field set and display it
    field_set = plugin(None, "file", stream)

    # Display the field set 
#    displayFieldSet(field_set, 1)

    # Metadata
    metadata = createMetaData(field_set)
    if metadata != None:
        print metadata
    else:
        warning("Can't create meta datas")

if __name__ == "__main__":
    main()

