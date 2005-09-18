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
    print "\t--server-log      : Output server log (default: %u)" % (defval["server-log"])
    print "\t--max-fps MAX     : Set maximum frame par second (fps)"
    print "\t--text            : Use text output"

def parseArgs(val):
    import getopt

    defval = val.copy()
    try:
        short = "h:dv"
        long = ["debug", "help", "version", "verbose", \
            "view-port=", "input-port=",
            "host=", "max-fps=", "server-log", "text"]
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
        if o == "--server-log":
            val["server-log"] = True
        if o == "--text":
            val["textmode"] = True
        if o == "--max-fps":
            a = int(a)
            if a < 1: a=1
            elif 100<a: a=100
            val["max_fps"] = a
        if o in ("-d", "--debug",):
            val["debug"] = True
    return val

def run(arg):
    from client import Client
    from happyboom.common.log import log
    
    client = Client(arg)
    try:
        client.start()
    except KeyboardInterrupt:
        log.warning("Program interrupted (CTRL+C).")
        pass
    client.stop()

def run_curses(stdscr, args):
    from happyboom.common.log import log
    try:
        args["window"] = stdscr
        stdscr.scrollok(True)
        run(args)
    except Exception, err:
        log.error("Uncatched error in run_curses: %s" % err)
        raise

def main():
    # Add HappyBoom to PYTHONPATH ("../" today, but should be improved)
    import sys, os
    file_dir = os.path.dirname(__file__)
    happyboomdir = os.path.join(file_dir, "../happyboom/trunk")
    sys.path.append(happyboomdir)

    # Get user directory 
    from happyboom.common.file import getCreateHomeDir
    logdir = getCreateHomeDir("boomboom")

    # Setup log filename
    from happyboom.common.log import log
    if logdir != None:
        logname = os.path.join(logdir, "client-log")    
        log.setFilename(logname)

    # Read command line arguments
    val = {
        "host": "127.0.0.1", \
        "port": 12430, \
        "max_fps": 50, \
        "verbose": False, \
        "textmode": False, \
        "server-log": False, \
        "name": "-", \
        "debug": False, \
        "item_path": "client/items"}
    arg = parseArgs(val)
    textmode = arg["textmode"]

    # Create the client
    if not textmode:
        log.info("Start client with pygame.")
        import pygame
        pygame.init()
        run(arg)
        pygame.quit()
    else:
        log.info("Start client with curses.")
        import curses
        curses.wrapper(run_curses, arg)
        log.use_print = True
    log.info("Quit.")

if __name__=="__main__": main()
