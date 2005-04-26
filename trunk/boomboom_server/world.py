from server import server_agent
import random

class Building:
	def __init__(self, x, height, width):
		self.x = x
		self.y = 350-height
		self.width = width
		self.height = height

class World(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "world")
		self.buildings = None
		
	# Generate world
	def start(self):
		server_agent.ServerAgent.start(self)
		width = 640
		x = 0
		self.buildings = []
		building_hmin = 100
		building_hmax = 350-100
		building_wmin = 40
		building_wmax = 60
		while building_wmin<width:
			w = random.randint(building_wmin, building_wmax)
			h = random.randint(building_hmin, building_hmax)
			building = Building(x, h, w)
			self.buildings.append(building)
			width = width - w
			x = x + w
		if 0 < width:
			h = random.randint(building_hmin, building_hmax)
			building = Building(x, h, width)
			self.buildings.append(building)

	def sync(self, client):
		msg = ""
		for b in self.buildings:
			if len(msg) != 0: msg = msg + ";"
			msg = msg + "%i,%i,%i,%i" % (b.x, b.y, b.width, b.height)
		self.sendMsg("world", "create", msg)
