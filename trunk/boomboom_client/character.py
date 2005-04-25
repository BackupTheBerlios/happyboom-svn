from view import *
import pygame

class VisualObject:
	def __init__(self, file):
		self.original = self.surface = pygame.image.load(file).convert_alpha()
		self.x, self.y = (0,0)
		self.angle = 0

	def move(self, x, y):
		self.x = x
		self.y = y
		
	def rotate(self, delta_angle):
		self.angle += delta_angle
		self.surface = pygame.transform.rotate(self.original, self.angle)
		
	def draw(self, screen):
		screen.surface.blit(self.surface, (self.x-screen.view_pos[0], self.y-screen.view_pos[1]))
		pass

class CharacterAgent(ViewAgent):
	def __init__(self, name):
		ViewAgent.__init__(self)
		self.x = None
		self.y = None
		self.id = None
		self.name = name
		self.msg_handler["character"] = {"move": self.evtMove}
		self.visual = None 

	def start(self):
		ViewAgent.start(self)	
		self.load(self.server.visual.db)
		self.server.visual.objects.append (self)

	def load(self, db):
		if self.server.getActiveCharacter() == self:
			file = "ball.png"
		else:
			file = "alien.png"
#		file = db[self.name]
		self.visual = VisualObject("boomboom_data/"+file)

	def evtMove(self, arg):
		arg = arg.split(",")
		if self.id != int(arg[0]): return
		self.x = int(arg[1])
		self.y = int(arg[2])
		self.visual.move(self.x, self.y)
		print "Move : %i,%i" % (self.x, self.y)

	def mydraw(self, screens):
		if self.x == None: return
		for screen in screens: self.visual.draw(screen)

	def draw(self, force=False):
		pass
