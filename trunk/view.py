from common import io
import time
import socket
from common import mailing_list
from view import *

class View:
	instance = None

	def __init__(self):
		View.instance = self
		self.io = None
		self.n = None
		self.agents = {}
		self.loop = True
		self.mailing_list = mailing_list.MailingList()
		self.on_recv_message = None

	def registerAgent(self, id, agent):
		agent.id = id
		agent.server = self
		self.agents[id] = agent
		print "****"
		agent.start()

	def start(self):
		self.io = io.ClientIO()
		self.io.start(12430)
		self.registerAgent(0, AgentManager() )

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

		print "\33[2J\33[1;1H"
		print "=== Cycle ==="
		for key in self.agents:	
			agent = self.agents[key]
			agent.draw()

	def stop(self):
		self.io.send("quit")
		self.io.stop()

def main():
	view = View()
	try:
		view.start()
	except socket.error:
		print "Connexion to server %s:%s failed !" % (view.io.host, view.io.port)
		return
		
	try:
		while view.loop==True:
			view.live()
			time.sleep(0.050)
	except KeyboardInterrupt:
		pass
	view.stop()
	print "View closed."

if __name__=="__main__": main()
