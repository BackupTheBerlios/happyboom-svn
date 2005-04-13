#!/usr/bin/python
from common import io
import socket

cmd_ok = ("quit", "+", "-")

def processCmd(cmd):
	global cmd_ok, io
	if cmd in cmd_ok: io.send(cmd+"\n")

def main():
	global io
	io = io.ClientIO()
	try:
		host = socket.gethostname()
		io.start(host, 12431)
	except socket.error:
		print "Connexion to server failed."
		return 
	
	ok = True
	print ""
	print "Commands :"
	print "* +     : increment controlable agent"
	print "* -     : increment controlable agent"
	print "* close : close input"
	print "* quit  : quit game"
	cmd=""
	while (cmd != "quit") & (cmd != "close"):
		cmd = raw_input("cmd ? ")
		processCmd(cmd)
	io.stop()
	print "Input closed."

if __name__=="__main__": main()
