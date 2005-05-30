from bb_agent import *

class CharacterAgent(BoomBoomAgent):
	def __init__(self, name):
		BoomBoomAgent.__init__(self)
		self.x = None
		self.y = None
		self.id = None
		self.name = name
		self.msg_handler["character"] = {"move": self.evtMove}
		self.visual = VisualObject("boomboom_data/gorilla.png")

	def start(self):
		BoomBoomAgent.start(self)	

	def evtMove(self, arg):
		arg = arg.split(",")
		if self.id != int(arg[0]): return
		self.x = int(arg[1])
		self.y = int(arg[2])
		self.visual.move(self.x, self.y)

	def draw(self, screen):
		if self.x==None: return
		self.visual.draw(screen)
