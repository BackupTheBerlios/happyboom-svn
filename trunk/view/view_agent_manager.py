import time
from view_agent import *
from view_chat import *
from view_debug import *
from view_number import *
from view_stats import *

class AgentManager(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.msg_handler = {\
			"agent_manager": {
				"Create": self.evtCreate, 
				"Text": self.recvText,
				"AskVersion": self.askVersion,
				"AskName": self.askName},
			"game": {
				"Start": self.gameStart,
				"Stop": self.gameStop}}
		self.iteration = 0
		self.time = time.time()
		self.messages = []
		self.max_messages = 5

	def start(self):
		ViewAgent.start(self)
		if self.server.stats:
			agent = NetworkStatAgent()
			self.server.registerAgent(1000, agent)
		if self.server.debug:
			agent = DebugMsgAgent()
			self.server.registerAgent(1001, agent)

	def recvText(self, msg):
		if self.max_messages == len(self.messages):
			del self.messages[0]
		self.messages.append(msg)
		if self.server.verbose: print "Server message: ",msg

	def askName(self, arg):
		self.server.send(self.server.name)
		
	def askVersion(self, arg):
		self.server.send(self.server.protocol_version)
		
	def tryCreateAgent(self, id, type):
		if (type=="server_stat") and \
		   (self.server.stats or self.server.only_whatch_server):
			return ViewServerStat()
		if self.server.only_whatch_server: return None
		if type=="number": return ViewN()
		if type=="chat_server": return ViewChat()
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
			self.server.send("yes")
			for role in agent.msg_handler:
				self.server.send(role)
			self.server.send(".")
		else:
			self.server.send("no")

	def draw(self):
		diff = time.time() - self.time
		if 2.5 <= diff:
			fps = "%.1f" % (self.iteration / diff)
		else:
			n = int(diff*2)
			fps = "*" * (n) + "." * (4-n)
		if not self.server.verbose:
			print "View: time=%u sec, fps=%s" % (diff, fps)
			for msg in self.messages:
				print "Server message: %s" % (msg)

	def live(self):
		self.processMessages()
		self.iteration = self.iteration + 1
