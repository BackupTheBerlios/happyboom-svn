from bb_agent import *
import pygame

class Sun(BoomBoomAgent):
	def __init__(self):
		BoomBoomAgent.__init__(self)
		self.msg_handler["projectile"] = {"move": self.evtMove}
		self.msg_handler["game"] = {"next_turn": self.evtNextTurn}
		self.visual1 = VisualObject("boomboom_data/sun.png")
		self.visual2 = VisualObject("boomboom_data/sun2.png")
		self.visual1.move (300,10)
		self.visual2.move (300,10)
		self.visual = self.visual1

	def evtNextTurn(self, arg):
		self.resetHit()
		
	def evtMove(self, arg):
		arg = arg.split(",")
		x = int(arg[0])
		y = int(arg[1])
		agent_rect = pygame.Rect( [x,y,10,10]) # TODO: Uncorrect projectile size!
		if self.visual.rect.colliderect(agent_rect):
			self.hit()

	def resetHit(self):
		self.visual = self.visual1
	
	def hit(self):
		self.visual = self.visual2

	def draw(self, screen):
		self.visual.draw(screen)
