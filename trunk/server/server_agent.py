from common import agent
import random
import time

class ServerAgent(agent.Agent):
	def __init__(self, type):
		agent.Agent.__init__(self)
		self.type = type
		self.id = -1 
		self.server = None

	def sendMsg(self, role, type, arg=None):
		self.server.sendMsg(role, type, arg)

class GameStateAgent(ServerAgent):
	def __init__(self):
		ServerAgent.__init__(self, "game_state")
		self.msg_handler = {"command": {"new": self.evtCommand}}

	def evtCommand(self, arg):
		if arg=="quit": self.server.quit = True

class AgentN(ServerAgent):
	def __init__(self, value=10000, delta=100):
		ServerAgent.__init__(self, "number")
		self.value = value
		self.delta = delta
		self.time = time.time()

	def update(self, n):
		self.value = n
		print "Agent (%u) new value = %i" % (self.id, self.value)
		self.sync()

	def sync(self):
		self.sendMsg("number", "Update", "%u,%i" % (self.id, self.value))

	def live(self):
		self.processMessages()
		if time.time() - self.time < 5: return
		self.time = time.time()

		delta = int( random.random() * self.delta )
		if (random.random() < 0.5):			
			self.update ( self.value + delta )
		else:
			self.update ( self.value - delta )

class ControlableAgentN(AgentN):
	def __init__(self, value=1000, delta=5):
		AgentN.__init__(self, value, delta)
		self.msg_handler["command"] = {"new": self.evtCommand}

	def evtCommand(self, arg):
		if arg=="+":
			print "[Controlabe] Add"
			self.update (self.value + self.delta)
		elif arg=="-":
			print "[Controlabe] Sub"
			self.update (self.value - self.delta)

	def live(self):
		self.processMessages()

class FollowAgentN(ServerAgent):
	def __init__(self, follow_agent):
		ServerAgent.__init__(self, "follow")
		self.value = 0
		self.follow_agent_id = follow_agent.id
		self.objective = None
		self.msg_handler["number"] = {"Update": self.evtSetObjective}

	def evtSetObjective(self, arg):
		arg = arg.split(",")
		if int(arg[0]) != self.follow_agent_id: return

		val = int(arg[1])
		if self.objective == None: self.value = val
		self.objective = val

	def update(self, val):
		self.value = val
		self.sync()

	def sync(self):
		self.sendMsg("follow", "Update", "%i" % self.value)		

	def live(self):
		agent.Agent.live(self)
		if self.objective == None: return
		if self.objective < self.value:
			self.update ( self.value - 1 )
		elif self.objective > self.value:
			self.update ( self.value + 1 )
