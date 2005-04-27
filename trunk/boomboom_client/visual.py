# Visual
# Boombastic - GPL licence 
import pygame

class BoomBoomVisual:
	def __init__(self):
		self.__screen = None
		self.objects = []

	def clear_screen(self):
		if self.__screen == None: return
		self.__screen.surface.fill (self.__screen.background_color)

	def render(self):
		if self.__screen == None: return
		for obj in self.objects:
			obj.draw(self.__screen)
		
		pygame.display.flip()

	def start(self, theme="2d_classic"):
		self.__screen = Window(640, 350)
		self.__screen.background_color = (0, 0, 168)

class Window:
	def __init__(self, width, height, type="window"):
		if type=="surface":
			self.type = "surface" 
			self.surface = pygame.Surface((width,height))
		else:
			self.type = "window"
			self.surface = pygame.display.set_mode((width,height))
		self.pos = (0,0)
		self.view_pos = (0,0)
		self.scale = 1
		self.border_color = (255, 255, 255)
		self.background_color = (0, 0, 0)

	def blit(self, surface, pos):
		new_pos = (pos[0] - self.view_pos[0], pos[1] - self.view_pos[1],)
		self.surface.blit(surface, new_pos)

