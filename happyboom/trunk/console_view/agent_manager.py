from view import *
from view_chat import *
from view_debug import *
from view_number import *
from view_stats import *

class ConsoleAgentManager(BaseAgentManager):
	def __init__(self):
		BaseAgentManager.__init__(self)
		self.msg_handler["game"] = {\
			"Start": self.gameStart,
			"Stop": self.gameStop}
		self.msg_handler["agent_manager"]["Text"] = self.recvText
		self.messages = []
		self.max_messages = 5
		
	def gameStart(self, arg):
		pass

	def gameStop(self, arg):
		self.server.loop = False

	def recvText(self, msg):
		if self.max_messages == len(self.messages):
			del self.messages[0]
		self.messages.append(msg)
		if self.server.verbose: print "Server message: ",msg
	
	def start(self):
		BaseAgentManager.start(self)
		if self.server.stats:
			agent = NetworkStatAgent()
			self.server.registerAgent(1000, agent)
		if self.server.debug:
			agent = DebugMsgAgent()
			self.server.registerAgent(1001, agent)

	def tryCreateAgent(self, id, type):
		if (type=="server_stat") and \
		   (self.server.stats or self.server.only_watch_server):
			return ViewServerStat()
		if self.server.only_watch_server: return None
		if type=="number": return ViewN()
		if type=="chat_server": return ViewChat()
		if type=="follow": return ViewFollowN()
		return None

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
