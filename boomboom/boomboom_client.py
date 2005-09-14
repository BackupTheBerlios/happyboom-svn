#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
VERSION="0.2.0"
PROGRAM="BoomBoom client"

import time
import socket
import sys

def usage(defval):
    print "%s version %s" % (PROGRAM, VERSION)
    print ""
    print "Usage: %s [options] [yourname]" % (sys.argv[0])
    print
    print "Options :"
    print "\t--help            : Print this help"
    print "\t--version         : Print the software version"
    print "\t-h,--host HOST    : Server ip/name (default %s)" % (defval["host"])
    print "\t--port PORT       : Server port (default %u)" % (defval["port"])
    print "\t-d,--debug        : Enable debug mode"
    print "\t-v,--verbose      : Enable verbose mode"
    print "\t--max-fps MAX     : Set maximum frame par second (fps)"

def parseArgs(val):
    import getopt

    defval = val.copy()
    try:
        short = "h:dv"
        long = ["debug", "help", "version", "verbose", \
            "view-port=", "input-port=",
            "host=", "max-fps="]
        opts, args = getopt.getopt(sys.argv[1:], short, long)
    except getopt.GetoptError:
        usage(defval)
        sys.exit(2)

    if 0<len(args): val["name"] = args[0]
        
    for o, a in opts:
        if o == "--help":
            usage(defval)
            sys.exit()
        if o == "--version":
            print "%s version %s" % (PROGRAM, VERSION)
        if o == "--port":
            val["port"] = int(a)
        if o in ("-h", "--host",):
            val["host"] = a
        if o in ("-v", "--verbose",):
            val["verbose"] = True
        if o == "--max-fps":
            a = int(a)
            if a < 1: a=1
            elif 100<a: a=100
            val["max_fps"] = a
        if o in ("-d", "--debug",):
            val["debug"] = True
    return val

def run(arg):
    from happyboom.common.protocol import loadProtocol
    from client import BoomBoomClient
    from client.bb_display import BoomBoomDisplay

    protocol = loadProtocol("protocol.xml")
    display = BoomBoomDisplay(protocol, arg)
    client = BoomBoomClient(display, arg)
    try:
        client.start()
    except KeyboardInterrupt:
        print "Program interrupted (CTRL+C)."
        pass
    client.stop()

def main():
    # Add HappyBoom to PYTHONPATH ("../" today, but should be improved)
    import sys, os
    file_dir = os.path.dirname(__file__)
    happyboomdir = os.path.join(file_dir, "../happyboom/trunk")
    sys.path.append(happyboomdir)
 
    val = {
        "host": "127.0.0.1", \
        "port": 12430, \
        "max_fps": 50, \
        "verbose": False, \
        "name": "-", \
        "debug": False}
    arg = parseArgs(val)

    # Create the client
    import pygame
    run(arg)
    pygame.quit()

if __name__=="__main__": main()
