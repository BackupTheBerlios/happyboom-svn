#!/usr/bin/python
VERSION="0.0.1"
PROGRAM_FULL_NAME="HappyBoom console viewer"

from common import io
import time
import socket
from common import mailing_list
from view import *
import sys

class View:
	instance = None

	def __init__(self):
		View.instance = self
		self.io = io.ClientIO()
		self.n = None
		self.agents = {}
		self.loop = True
		self.clear_screen = True
		self.mailing_list = mailing_list.MailingList()
		self.on_recv_message = None
		self.verbose = False
		self.debug = False
		self.max_fps = 25

	def registerAgent(self, id, agent):
		agent.id = id
		agent.server = self
		self.agents[id] = agent
		agent.start()

	def start(self, host, port):
		self.io.client.on_disconnect = self.on_disconnect
		self.io.start(host, port)
		self.registerAgent(0, AgentManager() )

	def on_disconnect(self):
		self.loop = False

	def str2msg(self, str):
		import re
		r = re.compile("^([^:]+):([^:]+)(:(.*))?$")
		regs = r.match(str)
		if regs == None: return None
		
		role = regs.group(1)
		type = regs.group(2)
		if 2<regs.lastindex:
			arg = regs.group(4)
		else:
			arg = None
		return AgentMessage(role, type, arg)

	def registerMessage(self, agent, role):
		self.mailing_list.register(role, agent)
	
	def processMessages(self, lines):
		for line in lines:
			msg = self.str2msg(line)
			if self.on_recv_message: self.on_recv_message (msg)
			if msg != None: 
				locals = self.mailing_list.getLocal(msg.role)
				for agent in locals:
					agent.putMessage(msg)
				
	def live(self):
		for key in self.agents:
			agent = self.agents[key]
			old_size = len(self.agents)
			agent.live()
			if len(self.agents) != old_size: break
			if self.loop==False: return
	
		lines = self.io.read()
		if lines!=None: self.processMessages(lines)
		if self.loop==False: return

		if self.clear_screen: print "\33[2J\33[1;1H"
		print "=== %s version %s ===" % (PROGRAM_FULL_NAME, VERSION)
		for key in self.agents:	
			agent = self.agents[key]
			agent.draw()
		
	def setDebugMode(self, debug):
		self.debug = debug

	def setVerbose(self, verbose):
		self.clear_screen = not verbose
		self.io.setVerbose(verbose)

	def stop(self):
		self.io.send("quit")
		self.io.stop()

def usage():
	print "%s version %s" % (PROGRAM_FULL_NAME, VERSION)
	print "Usage: %s [-h,--host <host>] [-v,--verbose] [-d,--debug] [--fps MAX_FPS]" \
		% (sys.argv[0])
	print
	print "Long arguments :"
	print "\t--help      : Show this help"
	print "\t--host HOST : Specify server address (IP or name)"
	print "\t--debug     : Enable debug mode"
	print "\t--verbose   : Enable verbose mode"
	print "\t--fps       : Set maximum frame par second (fps)"

def parseArgs(val):
	import getopt
	try:
		short = "h:dv"
		long = ["debug", "host=", "help", "verbose","fps="]
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
		if o == "--fps":
			a = int(a)
			if a < 1: a=1
			elif 100<a: a=100
			val["max_fps"] = a
		if o in ("-d", "--debug"):
			val["debug"] = True
	return val

def main():
	view = View()
	val = {
		"host": socket.gethostname(), \
		"port": 12430, \
		"max_fps": 50, \
		"verbose": False, \
		"debug": False}
	arg = parseArgs(val)

	try:
		# Connexion
		try:
			view.setDebugMode( arg["debug"] )
			view.setVerbose( arg["verbose"] )
			view.max_fps = arg["max_fps"]
			view.start(arg["host"], arg["port"])
		except socket.error:
			print "Connexion to server %s:%s failed !" % (view.io.host, view.io.port)
			return
	
		# Main loop
		while view.loop==True:
			view.live()
			time.sleep(1.0 / view.max_fps)
	except KeyboardInterrupt:
		print "Program interrupted."
		pass
	view.stop()
	print "View closed."

if __name__=="__main__": main()
