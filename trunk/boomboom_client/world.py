from bb_agent import *
import pygame
import random

class Building:
	def __init__(self, x, y, width, height):
		print "Create Building %s" % ([x, y, width, height]) 
		self.rect = pygame.Rect( [x, y, width, height] )
		self.color = (\
			random.randint(0,255), random.randint(0,255), \
			random.randint(0,255), 255,)

	def draw(self, screen):
		screen.surface.fill(self.color, self.rect)

class World(BoomBoomAgent):
	def __init__(self):
		BoomBoomAgent.__init__(self)
		self.msg_handler["world"] = {"create": self.evtCreate}
		self.buildings = []

	def evtCreate(self, msg):
		self.buildings = []
		rects = msg.split(";")
		print "Create World"
		for rect in rects:
			r = rect.split(",")
			b = Building( int(r[0]), int(r[1]), int(r[2]), int(r[3]))
			self.buildings.append (b)

	def draw(self, screen):
		for b in self.buildings: b.draw(screen)
