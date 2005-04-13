from agent import Agent, AgentMessage
import time

class ViewAgent(Agent):
	def __init__(self):
		Agent.__init__(self)
		self.server = None

	def draw(self):
		pass

class DebugMsgAgent(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.last_msg = []
		self.total_msg = 0
		self.keep_msg_nb = 10

	def start(self):
		self.server.on_recv_message = self.receiveMsg

	def receiveMsg(self, msg):
		self.total_msg = self.total_msg + 1
		if self.keep_msg_nb <= len(self.last_msg):
			del self.last_msg[0]
		self.last_msg.append (msg)

	def draw(self):
		print "Last messages (total=%u) :" % (self.total_msg)
		for msg in self.last_msg:
			print "* %s" % (msg.str())

class NetworkStatAgent(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.in_bytes = 0
		self.out_bytes = 0
		self.time = time.time()
		self.avg_in = 0
		self.avg_out = 0

	def start(self):
		self.server.io.on_read = self.on_read
		self.server.io.on_write = self.on_write

	def on_write(self, data):
		self.out_bytes = self.out_bytes + len(data)

	def on_read(self, data):
		self.in_bytes = self.in_bytes + len(data)

	def draw(self):
		print "Network stat: avg  in=%.1f KB/s out=%.1f KB/s" \
			% (self.avg_in / 1024, self.avg_out / 1024)
		print "Network stat: curr in=%s B, out=%s B" \
			% (self.in_bytes, self.out_bytes)

	def live(self):
		diff = time.time() - self.time
		self.avg_in = self.in_bytes / diff
		self.avg_out = self.out_bytes / diff

class ViewN(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.value = 1000
		self.msg_handler = {"number": {"Update": self.evtUpdate}}

	def evtUpdate(self, arg):
		arg = arg.split(",")
		if self.id != int(arg[0]): return
		self.value = int(arg[1])

	def live(self):
		self.processMessages()

	def draw(self):
		print "Number[%u]=%i" % (self.id, self.value)

class ViewFollowN(ViewN):
	def __init__(self):
		ViewN.__init__(self)
		self.msg_handler = {"follow": {"Update": self.evtUpdate}}
		
	def evtUpdate(self, arg):
		self.value = int(arg)

	def draw(self):
		print "Follow[%u] --> %i" % (self.id, self.value)

class AgentManager(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.msg_handler = {\
			"agent_manager": {"Create": self.evtCreate}, \
			"game": {"Start": self.gameStart, "Stop": self.gameStop}}
		self.iteration = 0
		self.time = time.time()

	def start(self):
		ViewAgent.start(self)
		if self.server.debug:
			agent = NetworkStatAgent()
			self.server.registerAgent(1000, agent)
			agent = DebugMsgAgent()
			self.server.registerAgent(1001, agent)
		
	def tryCreateAgent(self, id, type):
		if type=="number": return ViewN()
		if type=="follow": return ViewFollowN()
		return None

	def gameStart(self, arg):
		pass

	def gameStop(self, arg):
		self.server.loop = False

	def evtCreate(self, arg):
		arg = arg.split(":")
		type = arg[0]
		id = int(arg[1])
		agent = self.tryCreateAgent(id, type)
		if agent != None:
			self.server.registerAgent(id, agent)
			self.server.io.send("yes")
		else:
			self.server.io.send("no")

	def draw(self):
		diff = time.time() - self.time
		if 0 < diff:
			fps = "%.1f" % (self.iteration / diff)
		else:
			fps = "?"
		print "Game : iteration=%u, time=%u sec, fps=%s" \
			% (self.iteration, diff, fps)

	def live(self):
		self.processMessages()
		self.iteration = self.iteration + 1
