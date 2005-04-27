from server import server_agent

class CharacterAgent(server_agent.ServerAgent):
	def __init__(self, x, team):
		server_agent.ServerAgent.__init__(self, "character")
		self.x = x
		self.y = 0
		self.width = 28
		self.height = 29
		self.team = team

	def move(self, x, y, force=False):
		if self.x == x and self.y == y and not force: return
		self.x = x
		self.y = y
		self.sendMsg("character", "move", "%u,%i,%i" % (self.id, self.x, self.y))

	def sync(self, client=None):
		self.move(self.x, self.y, force=True)

	def findPlace(self, world):
		for b in world.buildings:
			ok = (self.x+self.width <= b.x+b.width)
			if ok and (self.width < b.width):
				self.x = int( b.x + (b.width - self.width) / 2 )
				self.y = b.y - self.height
				return	
