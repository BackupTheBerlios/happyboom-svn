from bb_agent import *
import pygame

class Projectile(BoomBoomAgent):
	def __init__(self):
		BoomBoomAgent.__init__(self)
		self.msg_handler["projectile"] = {\
			"move": self.evtMove,
			"hit_ground": self.evtHitGround,
			"activate": self.evtActivate}
		self.visual = VisualObject("boomboom_data/banana.png")
		self.active = False
		

	def evtHitGround(self, msg):
		print "Hit ground"
		# TODO: Graphic effect

	def evtActivate(self, msg):
		self.active = (msg=="1")
		self.visual.setVisibility(self.active)

	def evtMove(self, msg):
		msg = msg.split(",")
		self.visual.move ( int(msg[0]), int(msg[1]) )

	def draw(self, screen):
		self.visual.draw(screen)
