#!/usr/bin/python
VERSION="0.0.1"

from common import io
import socket
import sys

cmd_ok = ("quit", "+", "-")

def processCmd(cmd):
	global cmd_ok, io
	if cmd in cmd_ok: io.send(cmd+"\n")

def usage():
	print "HappyBoom input - version %s" % (VERSION)
	print "Usage: %s [-h <host>] [-d]" % (sys.argv[0])
	print
	print "Long arguments :"
	print "\t--help      : Show this help"
	print "\t--host HOST : Specify server address (IP or name)"
	print "\t--debug     : Enable debug mode"

def parseArgs(val):
	import getopt
	
	try:
		short = "h:d"
		long = ["debug", "host", "help"]
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

def main():
	global io
	io = io.ClientIO()
	val = {"host": socket.gethostname(), "port": 12431, "debug": False}
	arg = parseArgs(val)
	try:
		try:
			io.start(arg["host"], arg["port"])
		except socket.error:
			print "Connexion to server failed."
			return 
		
		ok = True
		displayCommands()
		cmd=""
		while (cmd != "quit") & (cmd != "close"):
			cmd = raw_input("cmd ? ")
			processCmd(cmd)
	except KeyboardInterrupt:
		print "Program interrupted."
		pass
	io.stop()
	print "Input closed."

if __name__=="__main__": main()
