#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
VERSION="0.2.0"
PROGRAM="BoomBoom"

import getopt
import sys

def usage(defval):
    print "%s server version %s" % (PROGRAM, VERSION)
    print ""
    print "Usage: %s [-v,--verbose] [-d,--debug] [-h,--help] [--version]" % (sys.argv[0])
    print ""
    print "Arguments :"
    print "\t-h,--help         : Show this help"
    print "\t--version         : Show the program version"
    print "\t-v,--verbose      : Activate verbose mode"
    print "\t-d,--debug        : Activate debug mode"
    print ""
    print "Other arguments :"
    print "\t--max-input NB    : Max input clients (default %u)" % (defval["maxInput"])
    print "\t--max-display NB     : Max display clients (default %u)" % (defval["maxDisplay"])
    print "\t--display-port PORT  : Port number for display clients (default %u)" % (defval["displayPort"])
    print "\t--input-port PORT : Port number for input clients (default %u)" % (defval["inputPort"])

def parseArgs(val):
    import getopt
    def_val = val.copy()
    
    try:
        short = "hdv"
        long = ["debug", "verbose", "help", "version", \
            "max-clients=",
            "client-port="]
        opts, args = getopt.getopt(sys.argv[1:], short, long)
    except getopt.GetoptError:
        usage(def_val)
        sys.exit(2)
    
    if 0<len(args):
        usage(def_val)
        sys.exit(2)
        
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(def_val)
            sys.exit()
        if o == "--version":
            print "%s server version %s" % (PROGRAM, VERSION)
            sys.exit()
        if o == "--client-port":
            val["client_port"] = int(a)
        if o == "--max-clients":
            a = int(a)
            if a < 1: 
                a = 1
            elif 100 < a:
                a = 100
            val["max_clients"] = a
        if o in ("-v", "--verbose"):
            val["verbose"] = True
        if o in ("-d", "--debug"):
            val["debug"] = True
    return val

def main():
    # Add HappyBoom to PYTHONPATH
    import sys, os
    file_dir = os.path.dirname(__file__)
    happyboomdir = os.path.join(file_dir, "..", "happyboom", "trunk")
    sys.path.append(happyboomdir)

    # Get user directory 
    from happyboom.common.file import getCreateHomeDir
    logdir = getCreateHomeDir("boomboom")

    # Setup log filename
    from happyboom.common.log import log
    if logdir != None:
        logname = os.path.join(logdir, "server-log")    
        log.setFilename(logname)
   
    # Read command line arguments
    val = { \
        "input_port": 12430,
        "max_clients": 4,
        "verbose": False,
        "debug": False}
    arg = parseArgs(val)
   
    # Create BoomBoom server
    from server.bb_server import Server
    from happyboom.common.protocol import loadProtocol
    protocol = loadProtocol("protocol.xml")
    server = Server(protocol, arg)

    # Main loop
    try:
        server.start()
    except KeyboardInterrupt:
        log.info("Program interrupted (CTRL+C).")
        pass
    
    # Stop the server
    server.stop()

if __name__=="__main__": main()
