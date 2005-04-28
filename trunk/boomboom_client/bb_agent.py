from view import *
import pygame

class VisualObject(object):
	def __init__(self, file):
		self.__x, self.__y = (0,0)
		self.loadImage(file)
		self.visible = True

	def loadImage(self, file):
		self.surface = pygame.image.load(file).convert_alpha()
		self.__width = self.surface.get_width()
		self.__height = self.surface.get_height()
		self.__rect = pygame.Rect( [self.__x, self.__y, self.__width, self.__height] )

	def move(self, x, y):
		self.__x = x
		self.__y = y
		self.__rect = pygame.Rect( [self.__x, self.__y, self.__width, self.__height] )

	def getRect(self):
		return self.__rect
	rect = property(getRect)
	
	def getHeight(self):
		return self.__height
	height = property(getHeight)
	
	def getWidth(self):
		return self.__width
	width = property(getWidth)
	
	def getX(self):
		return self.__x
	def setX(self, x):
		self.move(x, self.__y)
	x = property(getX,setX)
	
	def getY(self):
		return self.__y
	def setY(self, y):
		self.move(self.__x, y)
	y = property(getY,setY)

	def setVisibility(self, visible):
		self.visible = visible
		
	def draw(self, screen):
		if not self.visible: return
		screen.blit(self.surface, (self.x, self.y))

class BoomBoomAgent(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.is_visual = True

	def start(self):
		ViewAgent.start(self)
		if self.is_visual:
			self.server.visual.objects.append (self)

	def draw(self, screen):
		pass
