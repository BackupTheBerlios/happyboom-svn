#!/usr/bin/env python

VERSION = "0.2veryalpha"

from stream.file import FileStream
from text_ui import displayFieldSet
from plugin import loadPlugins, guessPlugin
from log import log
from error import error
from mime import getStreamMime
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
    if plugin != None:
        # Create field set and display it
        field_set = plugin(None, "file", stream)
        displayFieldSet(field_set, None)
#        meta = PngMetaData(png) ; print meta
#        meta = PcxMetaData(pcx) ; print meta
#        meta = BmpMetaData(bmp) ; print meta
    else:
        msg  = "Sorry, can't find plugin for file \"%s\"!" % filename
        mimes = [ mime[0] for mime in getStreamMime(stream, filename) ]
        msg += "\n\nFile mimes: %s" % ", ".join(mimes)
        error(msg)

if __name__ == "__main__":
    main()
