from view import *
from character import *
from game_state import *
from sun import *
from world import *

class BoomBoomAgentManager(BaseAgentManager):
	def __init__(self):
		BaseAgentManager.__init__(self)
		self.msg_handler["game"] = {\
			"Start": self.gameStart,
			"Stop": self.gameStop}
		self.msg_handler["agent_manager"]["Text"] = self.recvText
		self.messages = []
		self.max_messages = 5
		
	def gameStart(self, arg):
		agent = Sun()
		self.server.registerAgent(1000, agent)

	def gameStop(self, arg):
		self.server.loop = False

	def recvText(self, msg):
		if self.max_messages == len(self.messages):
			del self.messages[0]
		self.messages.append(msg)
		print "Server message: ",msg
	
	def start(self):
		BaseAgentManager.start(self)

	def tryCreateAgent(self, id, type):
		if type=="game_state":
			return GameStateAgent()
		if type=="world":
			return World()
		if type=="character":
			return CharacterAgent("foo")
		return None

	def draw(self):
		diff = time.time() - self.time
		if 2.5 <= diff:
			fps = "%.1f" % (self.iteration / diff)
		else:
			n = int(diff*2)
			fps = "*" * (n) + "." * (4-n)
		#print "View: time=%u sec, fps=%s" % (diff, fps)
