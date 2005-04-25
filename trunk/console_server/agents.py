import random
import time
from server import server_agent
import agent

class GameStateAgent(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "game_state")
		self.msg_handler = {"command": {"new": self.evtCommand}}

	def evtCommand(self, arg):
		if arg=="quit": self.server.quit = True

class AgentN(server_agent.ServerAgent):
	def __init__(self, value=10000, delta=100):
		server_agent.ServerAgent.__init__(self, "number")
		self.value = value
		self.delta = delta
		self.time = time.time()

	def update(self, n):
		self.value = n
		if self.server.verbose: print "Agent (%u) new value = %i" % (self.id, self.value)
		self.sync()

	def sync(self, client=None):
		self.sendMsg("number", "Update", "%u,%i" % (self.id, self.value), client=client)

	def live(self):
		self.processMessages()
		if time.time() - self.time < 5: return
		self.time = time.time()

		delta = int( random.random() * self.delta )
		if (random.random() < 0.5):			
			self.update ( self.value + delta )
		else:
			self.update ( self.value - delta )

class ChatAgent(server_agent.ServerAgent):
	def __init__(self, value=1000, delta=5):
		server_agent.ServerAgent.__init__(self, "chat_server")
		self.msg_handler["chat_server"] = {"new": self.newMessage}
		self.messages = []
		self.sync_message = 5 
		self.log_message = self.sync_message

	def sync(self, client=None):
		for msg in self.messages[-self.sync_message:]:
			self.sendMsg("chat", "message", msg)

	def newMessage(self, msg):
		if len(self.messages)==self.log_message: del self.messages[0]
		self.messages.append(msg)
		self.sendMsg("chat", "message", msg)
		if self.server.verbose: print "Chat message: %s" % (msg)

class ControlableAgentN(AgentN):
	def __init__(self, value=1000, delta=5):
		AgentN.__init__(self, value, delta)
		self.msg_handler["command"] = {"new": self.evtCommand}

	def evtCommand(self, arg):
		if arg=="+":
			if self.server.verbose: print "[Controlabe] Add"
			self.update (self.value + self.delta)
		elif arg=="-":
			if self.server.verbose: print "[Controlabe] Sub"
			self.update (self.value - self.delta)

	def live(self):
		self.processMessages()

class FollowAgentN(server_agent.ServerAgent):
	def __init__(self, follow_agent):
		server_agent.ServerAgent.__init__(self, "follow")
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

	def sync(self, client=None):
		self.sendMsg("follow", "Update", "%i" % self.value)		

	def live(self):
		server_agent.ServerAgent.live(self)
		if self.objective == None: return
		if self.objective < self.value:
			self.update ( self.value - 1 )
		elif self.objective > self.value:
			self.update ( self.value + 1 )
