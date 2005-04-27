from server import server_agent
import random

class Building:
	def __init__(self, world, x, height, width):
		self.world = world
		self.x = x
		self.y = self.world.height-height
		self.width = width
		self.height = height

	def isPartOf(self, x, y):
		if x<self.x: return False
		if self.x+self.width<x: return False
		if y<self.y: return False
		if self.y+self.height<y: return False
		return True

class World(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "world")
		self.buildings = None
		self.height = 350
		self.width = 640

	def hitGround(self, x, y):
		for b in self.buildings:
			if b.isPartOf(x,y): return True
		if self.height<=y: return True
		if x<0: return True
		if self.width<=x: return True
		return False
		
	# Generate world
	def start(self):
		server_agent.ServerAgent.start(self)
		width = self.width
		x = 0
		self.buildings = []
		building_hmin = 100
		building_hmax = self.height-100
		building_wmin = 40
		building_wmax = 60
		while building_wmin<width:
			w = random.randint(building_wmin, building_wmax)
			h = random.randint(building_hmin, building_hmax)
			building = Building(self, x, h, w)
			self.buildings.append(building)
			width = width - w
			x = x + w
		if 0 < width:
			h = random.randint(building_hmin, building_hmax)
			building = Building(self, x, h, width)
			self.buildings.append(building)

	def sync(self, client):
		msg = ""
		for b in self.buildings:
			if len(msg) != 0: msg = msg + ";"
			msg = msg + "%i,%i,%i,%i" % (b.x, b.y, b.width, b.height)
		self.sendMsg("world", "create", msg)
