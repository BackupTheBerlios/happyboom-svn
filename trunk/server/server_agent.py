from agent import *

class ServerAgent(Agent):
	def __init__(self, type):
		Agent.__init__(self)
		self.type = type
		self.id = -1 
		self.server = None

	def sendMsg(self, role, type, arg=None, client=None):
		if client != None:
			self.server.sendMsgToClient(client, role, type, arg)
		else:
			self.server.sendMsg(role, type, arg)
