from bb_agent import *

class CharacterAgent(BoomBoomAgent):
	def __init__(self, name):
		BoomBoomAgent.__init__(self)
		self.x = None
		self.y = None
		self.id = None
		self.name = name
		self.msg_handler["character"] = {"move": self.evtMove}
		self.visual = None 

	def start(self):
		BoomBoomAgent.start(self)	
		self.load(self.server.visual.db)

	def load(self, db):
#		if self.server.getActiveCharacter() == self:
#			file = "ball.png"
#		else:
#			file = "alien.png"
#		file = db[self.name]
		file = "gorilla.png"
		self.visual = VisualObject("boomboom_data/"+file)

	def evtMove(self, arg):
		arg = arg.split(",")
		if self.id != int(arg[0]): return
		self.x = int(arg[1])
		self.y = int(arg[2])
		self.visual.move(self.x, self.y)
		print "Move : %i,%i" % (self.x, self.y)

	def draw(self, screen):
		self.visual.draw(screen)
