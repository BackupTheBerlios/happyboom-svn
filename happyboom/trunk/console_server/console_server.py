from server import base_server
from server import stat
from agents import *
import re

class ConsoleServer(base_server.BaseServer):
	def __init__(self):
		base_server.BaseServer.__init__(self)

	# Create all agents
	def createAgents(self):
		self.agents = []
	
		agent = GameStateAgent()
		self.registerAgent( agent )
		
		agent = AgentN(1000, 100)
		self.registerAgent( agent )
		
		agent = FollowAgentN(agent)
		self.registerAgent( agent )

		agent = ChatAgent()
		self.registerAgent( agent )

		agent = ControlableAgentN(4000, 20)
		self.registerAgent( agent )

		agent = stat.ServerStatAgent()
		self.registerAgent( agent )

	def processInputCmd(self, input, cmd):
		if self.verbose:
			print "Command from %s: %s" % (input.name, cmd)
		r = re.compile("^chat:(.*)$")
		r = r.match(cmd)
		if r != None:
			print "New chat message: %s" % (r.group(1))
			self.sendMsg("chat_server", "new", r.group(1))
		elif cmd == "quit": self.sendMsg ("command", "new", cmd)
		elif cmd == "+": self.sendMsg ("command", "new", cmd)
		elif cmd == "-": self.sendMsg ("command", "new", cmd)
