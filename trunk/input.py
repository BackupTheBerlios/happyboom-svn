#!/usr/bin/python
VERSION="0.0.1"

from common import io
import socket
import sys

def usage():
	print "HappyBoom input - version %s" % (VERSION)
	print ""
	print "Usage: %s [-h <host>] [-dv]" % (sys.argv[0])
	print "\t--help      : Show this help"
	print "\t--host HOST : Specify server address (IP or name)"
	print "\t--debug     : Enable debug mode"
	print "\t--verbose   : Enable verbose mode"

def parseArgs(val):
	import getopt
	
	try:
		short = "h:dv"
		long = ["debug", "host", "help", "verbose"]
		opts, args = getopt.getopt(sys.argv[1:], short, long)
	except getopt.GetoptError:
		usage()
		sys.exit(2)
		
	for o, a in opts:
		if o == "--help":
			usage()
			sys.exit()
		if o in ("-h", "--host"):
			val["host"] = a
		if o in ("-v", "--verbose"):
			val["verbose"] = True
		if o in ("-d", "--debug"):
			val["debug"] = True
	return val

def displayCommands():
	print ""
	print "Commands :"
	print "* +     : increment controlable agent"
	print "* -     : increment controlable agent"
	print "* close : close input"
	print "* quit  : quit game"

class Input:
	def __init__(self):
		self.io = io.ClientIO()
		self.cmd_ok = ("quit", "+", "-")

	def setDebugMode(self, debug):
		if debug: print "*** Debug mode ***"

	def setVerbose(self, verbose):
		self.io.setVerbose(verbose)

	def processCmd(self, cmd):
		if cmd in self.cmd_ok:
			self.io.send(cmd+"\n")

	def stop(self):
		self.io.stop()

def main():
	val = { \
		"host": socket.gethostname(), \
		"port": 12431, \
		"verbose": False, \
		"debug": False}
	arg = parseArgs(val)
	input = Input()

	try:
		try:
			input.setDebugMode (arg["debug"])
			input.setVerbose (arg["verbose"])
			input.io.start(arg["host"], arg["port"])
		except socket.error:
			print "Connexion to server %s failed." % (input.io.host)
			return 
		
		displayCommands()
		cmd=""
		while (cmd != "quit") & (cmd != "close"):
			cmd = raw_input("cmd ? ")
			input.processCmd(cmd)

	except KeyboardInterrupt:
		print "Program interrupted."
		pass
	input.stop()
	print "Input closed."

if __name__=="__main__": main()
