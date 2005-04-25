# Visual
# Boombastic - GPL licence 
import pygame

class BoomBoomVisual:
	def __init__(self):
		self.screens = []
		self.db = None
		self.objects = []

	def render(self):
		for screen in self.screens: screen.surface.fill (screen.background_color)
		for obj in self.objects: obj.mydraw(self.screens)
		
		for screen in self.screens[1:]:
			x,y = screen.view_pos
			width,height = screen.surface.get_width(), screen.surface.get_height()
			rect_rect = pygame.Rect(x, y, width, height)
			pygame.draw.rect(screens[0].surface, screen.border_color, rect_rect, 1)
		
			out = screen.surface
			rect = out.get_rect()
			size = (width*screen.scale, height*screen.scale)
			out = pygame.transform.scale(out, size)
			rect = rect.move(screen.pos[0],screen.pos[1])
			screens[0].surface.blit(out, rect)

		pygame.display.flip()
		
	def init_screens_classic(self):
		main = Window(400, 400)
		main.background_color = (0, 0, 255)
		self.screens = [main]

	def init_screens_fun(self):
		# Main window
		main = Window(400, 400)
		main.background_color = (0, 0, 255)
		self.screens = [main]

		# Viewpoint #2
		screen = Window(100, 100, "surface")
		screen.pos = (200,200)
		screen.view_pos = (100,100)
		screen.scale = 2
		screen.background_color = (0, 255, 0)
		screen.border_color = (255, 255, 255)
		self.screens.append (screen)
		
		# Viewpoint #3
		screen = Window(30, 30, "surface")
		screen.pos = (0,300)
		screen.view_pos = (90,75)
		screen.scale = 3
		screen.background_color = (0, 100, 0)
		screen.border_color = (255, 255, 0)
		self.screens.append (screen)

	def start(self, theme="2d_classic"):
		self.db = dict() 
		if theme=="2d_fun":
			self.init_screens_fun()
			self.db["foo"] = "alien.png"
		else:
			self.init_screens_classic()
			self.db["foo"] = "ball.png"

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
