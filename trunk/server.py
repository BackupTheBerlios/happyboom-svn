#!/usr/bin/python
import time
import random
from net import net_server
from server import *
from common import mailing_list

def syncNewClient(client):
	Server.instance.registerNetMessage (client, "agent_manager")
	Server.instance.registerNetMessage (client, "number")
	Server.instance.registerNetMessage (client, "follow")
	Server.instance.registerNetMessage (client, "game")
	for agent in Server.instance.agents:
		msg = Server.instance.createMsg("agent_manager", "Create", "%s:%u" % (agent.type, agent.id))
		client.send (msg)
		answer = client.read()
		if answer == "yes": agent.sync()
	client.send ( Server.instance.createMsg("game", "Start") )

class Server:
	instance = None
	
	def __init__(self):
		Server.instance = self
		self.agents = []
		self.__view_io = None
		self.__input_io = None
		self.mailing_list = mailing_list.MailingList()
		self.net_mailing_list = {}
		self.cmd_handler = {}
		self.quit = False

	def createMsg(self, role, type, arg=None):
		if arg != None:
			return "%s:%s:%s\n" % (role, type, arg)
		else:
			return "%s:%s\n" % (role, type)

	def registerNetMessage(self, client, role):
		self.mailing_list.registerNet(role, client)

	def registerMessage(self, agent, role):
		self.mailing_list.register(role, agent)

	def createAgents(self):
		self.agents = []
	
		agent = GameStateAgent()
		self.registerAgent( agent )
		
		agent = AgentN(1000, 10)
		self.registerAgent( agent )
		
		agent = FollowAgentN(agent)
		self.registerAgent( agent )

		agent = ControlableAgentN(4000, 20)
		self.registerAgent( agent )

	def initIO(self):
		self.__view_io = net_server.NetworkServer(12430)
		self.__view_io.on_client_connect = syncNewClient
		self.__view_io.start()

		self.__input_io = net_server.NetworkServer(12431)
		self.__input_io.start()

	def start(self):
		self.createAgents()
		self.initIO()
		print "Server started."

	def connectAgent(self, cmd, agent):
		if self.cmd_handler.has_key(cmd):
			self.cmd_handler[cmd].append (agent)
		else:
			self.cmd_handler[cmd] = [agent]
		
	def registerAgent(self, agent):
		agent.id = 1+len(self.agents)
		agent.server = self
		self.agents.append(agent)
		agent.start()

	def sendMsg(self, role, type, arg=None):
		msg = AgentMessage(role, type, arg)
		locals = self.mailing_list.getLocal(role)
		for agent in locals:
			agent.putMessage(msg)
		
		msg = self.createMsg(role, type, arg)
		clients = self.mailing_list.getNet(role)
		for client in clients: client.send(msg)
		
	def processCmd(self, cmd):
		print "Received %s." % (cmd)
		if self.cmd_handler.has_key(cmd):
			for agent in self.cmd_handler[cmd]:
				print "Send %s to agent %u." % (cmd, agent.id)
				msg = AgentMessage(agent.id, "Command", cmd)
				agent.putMessage(msg)
		
	def processInputs(self):
		for input in self.__input_io.clients:
			data = input.readNonBlocking()
			if data != None:
				cmds = data.split("\n")
				for cmd in cmds:
					if cmd == "quit": self.sendMsg ("command", "new", cmd)
					if cmd == "+": self.sendMsg ("command", "new", cmd)
					if cmd == "-": self.sendMsg ("command", "new", cmd)

	def live(self):
		self.processInputs()
		for agent in self.agents:
			agent.live()
			if self.quit==True: break

	def stop(self):
		self.sendMsg("game", "Stop")
		self.agents = {}				

def main():
	random.seed()
	server = Server()
	server.start()
	try:
		while server.quit==False:
			server.live()
			time.sleep(0.010)
	except KeyboardInterrupt:
		pass
	server.stop()
	print "Server quit."

if __name__=="__main__": main()
