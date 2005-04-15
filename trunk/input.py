#!/usr/bin/python
VERSION="0.1.4"

import sys
import time
from input import hb_input

def usage(defval):
	print "HappyBoom input version %s" % (VERSION)
	print ""
	print "Usage: %s [options] [yourname]" % (sys.argv[0])
	print ""
	print "Options :"
	print "\t--help         : Show this help"
	print "\t-h,--host HOST : Server name/ip (default %s)" % (defval["host"])
	print "\t-p,--port PORT : Server port (default %u)" % (defval["port"])
	print "\t-d,--debug     : Enable debug mode"
	print "\t-v,--verbose   : Enable verbose mode"
	print "\t--readline     : Use readline (better input library)"

def parseArgs(val):
	import getopt
	
	defval = val.copy()
	try:
		short = "h:p:dv"
		long = ["debug", "port=", "host=", "help", "verbose", "readline"]
		opts, args = getopt.getopt(sys.argv[1:], short, long)
	except getopt.GetoptError:
		usage(defval)
		sys.exit(2)
	
	if 0<len(args): val["name"] = args[0]	

	for o, a in opts:
		if o == "--help":
			usage(defval)
			sys.exit()
		if o in ("-p", "--port"):
			val["port"] = int(a)
		if o in ("-h", "--host"):
			val["host"] = a
		if o in ("-v", "--verbose"):
			val["verbose"] = True
		if o in ("-d", "--debug"):
			val["debug"] = True
		if o == "--readline":
			val["readline"] = True
	return val

def displayCommands():
	print "Commands :"
	print ""
	print "* +        : increment controlable agent"
	print "* -        : increment controlable agent"
	print "* close    : close input"
	print "* quit     : quit game"
	print "* chat:MSG : Send messages"

def main():
	arg = { \
		"host": "127.0.0.1",
		"port": 12431,
		"name": "no name",
		"verbose": False,
		"readline": False,
		"debug": False}
	arg = parseArgs(arg)
	input = hb_input.Input()
	input.io.name = arg["name"]
	input.setDebugMode (arg["debug"])
	input.setVerbose (arg["verbose"])
	print arg["readline"]
	input.reader.use_readline = arg["readline"]

	try:
		input.start(arg["host"], arg["port"])
	
		if input.quit == False:
			displayCommands()
			while input.quit == False:
				input.live()
				time.sleep(0.100)

	except KeyboardInterrupt:
		print "Program interrupted (CTRL+C)."
		pass
	input.stop()

if __name__=="__main__": main()
