#!/usr/bin/python
VERSION="0.1.4"
import time
import random
from server import hb_server
import getopt
import sys

def usage(defval):
	print "HappyBoom server version %s" % (VERSION)
	print ""
	print "Usage: %s [-v,--verbose] [-d,--debug] [-h,--help]" % (sys.argv[0])
	print ""
	print "Arguments :"
	print "\t-h,--help         : Show this help"
	print "\t-v,--verbose      : Activate verbose mode"
	print "\t-d,--debug        : Activate debug mode"
	print ""
	print "Other arguments :"
	print "\t--max-input NB    : Max input clients (default %u)" % (defval["max-input"])
	print "\t--max-view NB     : Max view clients (default %u)" % (defval["max-view"])
	print "\t--view-port PORT  : Port number for view clients (default %u)" % (defval["view-port"])
	print "\t--input-port PORT : Port number for input clients (default %u)" % (defval["input-port"])

def parseArgs(val):
	import getopt
	def_val = val.copy()
	
	try:
		short = "hdv"
		long = ["debug", "verbose", "help", \
			"max-input=", "max-view=", \
			"view-port=", "input-port="]
		opts, args = getopt.getopt(sys.argv[1:], short, long)
	except getopt.GetoptError:
		usage(def_val)
		sys.exit(2)
		
	for o, a in opts:
		if o == "--help":
			usage(def_val)
			sys.exit()
		if o == "--input-port":
			a = int(a)
			if a == val["view-port"]:
				print "Sorry, input port should be different than view port!"
			else:
				val["input-port"] = a 			
		if o == "--view-port":
			a = int(a)
			if a == val["input-port"]:
				print "Sorry, view port should be different than input port!"
			else:
				val["view-port"] = a 
		if o == "--max-input":
			a = int(a)
			if a < 1: 
				a=1
			elif 100 < a:
				a = 100
			val["max-input"] = a
		if o == "--max-view":
			a = int(a)
			if a < 1: 
				a=1
			elif 100 < a:
				a = 100
			val["max-view"] = a
		if o in ("-v", "--verbose"):
			val["verbose"] = True
		if o in ("-d", "--debug"):
			val["debug"] = True
	return val

def main():
	val = { \
		"view-port": 12430, \
		"input-port": 12431, \
		"max-input": 4, \
		"max-view": 4, \
		"verbose": False,
		"debug": False}
	arg = parseArgs(val)
	
	server = hb_server.Server()
	server.setVerbose(arg["verbose"])
	server.setDebug(arg["debug"])

	random.seed()
	server.start(arg)
	try:
		while server.quit==False:
			server.live()
			time.sleep(0.010)
	except KeyboardInterrupt:
		print "Program interrupted (CTRL+C)."
		pass
	server.stop()
	print "Server quit."

if __name__=="__main__": main()
