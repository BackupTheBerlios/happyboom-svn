from bb_agent import *
import pygame

class Projectile(BoomBoomAgent):
	def __init__(self):
		BoomBoomAgent.__init__(self)
		self.msg_handler["projectile"] = {\
			"move": self.evtMove, "activate": self.evtActivate}
		self.visual = VisualObject("boomboom_data/banana.png")
		self.active = False
		self.x, self.y = None, None

	def evtActivate(self, msg):
		print "Activate : %s" % (msg)
		self.active = (msg=="1")

	def evtMove(self, msg):
		print "Move : %s" % (msg)
		msg = msg.split(",")
		self.visual.move ( int(msg[0]), int(msg[1]) )

	def draw(self, screen):
		if not self.active: return
		self.visual.draw(screen)
