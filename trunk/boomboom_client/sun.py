from bb_agent import *
import pygame

class Sun(BoomBoomAgent):
	def __init__(self):
		BoomBoomAgent.__init__(self)
		self.msg_handler["character"] = {"move": self.evtMove}
		self.visual1 = VisualObject("boomboom_data/sun.png")
		self.visual2 = VisualObject("boomboom_data/sun2.png")
		self.visual1.move (300,10)
		self.visual2.move (300,10)
		self.visual = self.visual1
		
	def evtMove(self, arg):
		arg = arg.split(",")
		agent_id = int(arg[0])
		agent = self.server.getAgent(agent_id)
		if agent == None: return
		x = int(arg[1])
		y = int(arg[2])
		agent_rect = pygame.Rect( [x,y,agent.visual.width,agent.visual.height])
		if self.visual.rect.colliderect(agent_rect):
			self.evtHit(agent)

	def resetHit(self):
		self.visual = self.visual1
	
	def evtHit(self, agent):
		print "Hit agent[id=%s] !" % (agent.id)
		self.visual = self.visual2

	def draw(self, screen):
		self.visual.draw(screen)
