#!/usr/bin/env python

VERSION = "0.2veryalpha"

from stream.file import FileStream
from text_ui import displayFieldSet
from plugin import loadPlugins, guessPlugin
from log import log
from error import error
from mime import getStreamMime
from metadata import createMetaData
import sys, os

def usage():
    print "Hachoir version %s" % VERSION
    print
    print "Usage: %s filename" % sys.argv[0]

def main():
    root_dir = os.path.dirname(__file__)

    # Create input stream (read filename from command line first argument)
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    filename = sys.argv[1]
    stream = FileStream(open(filename, 'r'), filename)

    # Load plugings
    modules = loadPlugins(os.path.join(root_dir, "file"))
    modules.sort()
    log.info("Loaded: %u plugings (%s)" % (len(modules), ", ".join(modules)))

    # Look for right plugin
    plugin = guessPlugin(stream, filename, None)
    if plugin == None:
        msg  = "Sorry, can't find plugin for file \"%s\"!" % filename
        mimes = [ mime[0] for mime in getStreamMime(stream, filename) ]
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
