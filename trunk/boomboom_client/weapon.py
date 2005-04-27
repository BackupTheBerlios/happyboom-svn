from bb_agent import *
import pygame

class Weapon(BoomBoomAgent):
	def __init__(self):
		BoomBoomAgent.__init__(self)
		self.msg_handler["weapon"] = {\
			"force": self.updateForce,
			"angle": self.updateAngle}
		self.angle = None 
		self.force = None
		fontname = pygame.font.get_default_font()
		self.font = pygame.font.SysFont(fontname, 14)
		self.font_color = (255,255,255,255)
		self.font_background = (0,0,0,0)
		self.y = 10

	def updateAngle(self, angle):
		self.angle = int(angle)
		print "Angle = %s" % (self.angle)

	def updateForce(self, force):
		self.force = int(force)

	def draw(self, screen):
		if self.angle == None: return
		if self.force == None: return
		txt = "Angle = %s, force=%s" % (self.angle, self.force)
		surface = self.font.render(txt, True, self.font_color, self.font_background)
		character = self.server.getActiveCharacter()
		if (character != None) and (character.x != None):
			x = character.x
		else:
			x = 10
		screen.blit (surface, (x,self.y))
