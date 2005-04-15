#!/usr/bin/python
VERSION="0.1.4"
PROGRAM_FULL_NAME="HappyBoom console viewer"

import time
import socket
import sys
from view import hb_view

def usage(defval):
	print "%s version %s" % (PROGRAM_FULL_NAME, VERSION)
	print ""
	print "Usage: %s [options] name" % (sys.argv[0])
	print
	print "Options :"
	print "\t--help          : Show this help"
	print "\t-h,--host HOST  : Server ip/name (default %s)" % (defval["host"])
	print "\t-p,--port PORT  : Server port (default %u)" % (defval["port"])
	print "\t--stats         : Display a lot of stats"
	print "\t--whatch-server : Only display server stats"
	print "\t-d,--debug      : Enable debug mode"
	print "\t-v,--verbose    : Enable verbose mode"
	print "\t--max-fps MAX   : Set maximum frame par second (fps)"

def parseArgs(val):
	import getopt

	defval = val.copy()
	try:
		short = "h:p:dv"
		long = ["debug", "help", "verbose" \
			"port=", "host=", "max-fps=", 
			"stats", "whatch-server"]
		opts, args = getopt.getopt(sys.argv[1:], short, long)
	except getopt.GetoptError:
		usage(defval)
		sys.exit(2)

	if len(args)==0:
		usage(defval)
		sys.exit(2)
	else:
		val["name"] = args[0]
		
	for o, a in opts:
		if o == "--help":
			usage(defval)
			sys.exit()
		if o in ("-p", "--port",):
			val["port"] = int(a)
		if o in ("-h", "--host",):
			val["host"] = a
		if o == "--stats":
			val["stats"] = True
		if o in ("-v", "--verbose",):
			val["verbose"] = True
		if o == "--max-fps":
			a = int(a)
			if a < 1: a=1
			elif 100<a: a=100
			val["max_fps"] = a
		if o == "--whatch-server":
			val["whatch-server"] = True
		if o in ("-d", "--debug",):
			val["debug"] = True
	return val

def main():
	val = {
		"host": "127.0.0.1", \
		"port": 12430, \
		"max_fps": 50, \
		"stats": False, \
		"verbose": False, \
		"name": "no name", \
		"whatch-server": False, \
		"debug": False}
	arg = parseArgs(val)
	
	view = hb_view.View()
	view.name = val["name"]
	view.setDebugMode( arg["debug"] )
	view.setVerbose( arg["verbose"] )
	view.only_whatch_server = arg["whatch-server"]
	if view.only_whatch_server:
		view.stats = False 
		view.max_fps = 5 
	else:
		view.stats = arg["stats"]
		view.max_fps = arg["max_fps"]

	try:
		# Try to connect to server
		try:
			view.start(arg["host"], arg["port"])
		except socket.error:
			print "Connection to server %s:%s failed !" % (view.io.host, view.io.port)
			return
	
		# Main loop
		while view.loop==True:
			view.live()

	except KeyboardInterrupt:
		print "Program interrupted (CTRL+C)."
		pass
	view.stop()

if __name__=="__main__": main()
