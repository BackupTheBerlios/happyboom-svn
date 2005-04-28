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
		self.x, self.y = None, None
		

	def evtHitGround(self, msg):
		print "Hit ground"
		# TODO: Graphic effect

	def evtActivate(self, msg):
		print "Activate : %s" % (msg)
		self.active = (msg=="1")
		if self.active==False:
			self.x, self.y = None, None

	def evtMove(self, msg):
		msg = msg.split(",")
		self.visual.move ( int(msg[0]), int(msg[1]) )

	def draw(self, screen):
		if not self.active: return
		if self.x==None: return
		self.visual.draw(screen)
