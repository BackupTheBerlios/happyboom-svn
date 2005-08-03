#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
VERSION="0.2.0"
PROGRAM="BoomBoom client"

import time
import socket
import sys
from client import BoomBoomClient

def usage(defval):
	print "%s version %s" % (PROGRAM, VERSION)
	print ""
	print "Usage: %s [options] [yourname]" % (sys.argv[0])
	print
	print "Options :"
	print "\t--help            : Print this help"
	print "\t--version         : Print the software version"
	print "\t-h,--host HOST    : Server ip/name (default %s)" % (defval["host"])
	print "\t--view-port PORT  : Server view port (default %u)" % (defval["view_port"])
	print "\t--input-port PORT : Server input port (default %u)" % (defval["input_port"])
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
		if o == "--input-port":
			val["input_port"] = int(a)
		if o == "--view-port":
			val["view_port"] = int(a)
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

def main():
	val = {
		"host": "127.0.0.1", \
		"view_port": 12430, \
		"input_port": 12431, \
		"max_fps": 50, \
		"verbose": False, \
		"name": "-", \
		"debug": False}
	arg = parseArgs(val)

	client = BoomBoomClient(arg["host"], arg["view_port"], arg["input_port"],\
							 arg["verbose"], arg["debug"], arg["max_fps"])
	try:
		client.start()
	except KeyboardInterrupt:
		print "Program interrupted (CTRL+C)."
		pass
	client.stop()

if __name__=="__main__": main()
