import time
from view_agent import *

class BaseAgentManager(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.msg_handler = {\
			"agent_manager": {
				"Create": self.evtCreate, 
				"AskVersion": self.askVersion,
				"AskName": self.askName}}
		self.iteration = 0
		self.time = time.time()

	def askName(self, arg):
		self.server.send(self.server.name)
		
	def askVersion(self, arg):
		self.server.send(self.server.protocol_version)
	
	def tryCreateAgent(self, id, type):
		return None

	def evtCreate(self, arg):
		arg = arg.split(":")
		type = arg[0]
		id = int(arg[1])
		agent = self.tryCreateAgent(id, type)
		if agent != None:
			self.server.registerAgent(id, agent)
			self.server.send("yes")
			for role in agent.msg_handler:
				self.server.send(role)
			self.server.send(".")
		else:
			self.server.send("no")

	def draw(self):
		pass

	def live(self):
		self.processMessages()
		self.iteration = self.iteration + 1
